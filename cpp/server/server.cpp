
#include "headers/server.hpp"
#include "headers/utils.hpp"

#include <arpa/inet.h>
#include <ctime>
#include <errno.h>
#include <iostream>
#include <memory.h>
#include <netdb.h>
#include <netinet/in.h>
#include <poll.h>
#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#include <sys/types.h>
#include <thread>
#include <unistd.h>

#define TIMEOUT_SUS 	15
#define TIMEOUT_KILL 	30
#define CHECK_INACTIVITY true


Server::Server (): Server {(char *)"12345"}
{

}

Server::Server (char *port)
{
	struct addrinfo 		hints, *gai, *ai;
	int						err;
	int						yes;

	yes = 1;
	
	bzero (&hints, sizeof (hints));

	hints.ai_family = AF_UNSPEC;
	hints.ai_socktype = SOCK_STREAM;
	hints.ai_flags = AI_PASSIVE;

	if ((err = getaddrinfo (NULL, port, &hints, &gai)) < 0)
	{
		fprintf (stderr, "getaddrinfo: %s\n", gai_strerror (err));
		exit (EXIT_FAILURE);
	}

	for (ai = gai; ai != NULL; ai = ai->ai_next)
	{
		if ((m_socket = socket (ai->ai_family, ai->ai_socktype, ai->ai_protocol)) < 0)
		{
			perror ("socket");
			continue;
		}
		
		if (setsockopt (m_socket, SOL_SOCKET, SO_REUSEADDR, &yes, sizeof (int)) < 0)
		{
			perror ("setsockopt");
			exit (EXIT_FAILURE);
		}

		if (bind (m_socket, ai->ai_addr, ai->ai_addrlen) < 0)
		{
			close (m_socket);
			perror ("server");
			continue;
		}

		break;
	}

	freeaddrinfo (gai);

	if (ai == NULL)
	{
		perror ("Failed to bind server");
		exit (EXIT_FAILURE);
	}

	m_id_counter = 0;

	fprintf (stderr, "Server created on port: %s\n", port);
}

Server::~Server ()
{
	if (m_socket) close (m_socket);
}

/*
	WARNNING : Should lock `m_clients_mutex` and `m_observer_mutex` before using this method
*/
Client &Server::RegisterClient (int fd, Client data)
{
	if (m_clients.find (fd) != m_clients.end ()) 
	{
		fprintf (stderr, "Client could not be registered as its file descriptor is already registered.");
		exit (EXIT_FAILURE);
	}

	m_observers.push_back ({fd, POLLIN});
	m_clients.insert ({fd, data});

	return (m_clients [fd]);
}

/*
	WARNING : Should lock `m_clients_mutex` and `m_observer_mutex` before using this method
*/
void Server::UnregisterClient (int fd)
{
	if (m_clients.find (fd) == m_clients.end ())
	{
		fprintf (stderr, "Client cannot be removed as its file descriptor is not registered.");
	}

	Client *client = &m_clients [fd];

	REQUEST_CALLBACK disconnect = m_protocol.GetDisconnectionRule ();
	disconnect ({}, *client);

	m_clients.erase (fd);

	close (fd);

	for (int i = 0; i < m_observers.size (); ++i)
	{
		if (m_observers [i].fd == fd)
		{
			m_observers [i] = m_observers.back ();
			m_observers.pop_back ();
			return;
		}
	}
}

void Server::HandleClient (Client &client, std::string request)
{
	client.UpdateActivity ();

	trim (request);
	if (request == "") return;

	fprintf (stderr, "Client [%d] %s\n", client.GetID (), request.c_str ());

	std::vector<std::string> buffered = split (request, "\n");

	for (auto& r : buffered)
	{
		if (client.IsTalking ())
		{
			REQUEST_CALLBACK& rule = m_protocol.GetTalkRule ();
			std::string answer = rule ({r}, client);
			trim (answer);
			Broadcast (client, answer);

			continue;
		}

		auto tokens = m_protocol.GetTokens (r);
		REQUEST_CALLBACK& rule = m_protocol.GetRule (tokens [0]);
	
		std::string answer = rule (tokens, client);
		Broadcast (client, answer);
	}

}

void Server::SetProtocol (Protocol protocol)
{
	m_protocol = protocol;
}

void Server::Broadcast (Client &client, std::string message)
{
	if (message == "") return;

	message += "\n";

	if (write (client.GetSocket (), message.c_str (), message.length ()) <= 0)
	{
		return;
	}
}

void Server::Listen ()
{
	sockaddr_storage	from;
	int					len;
	int					client_socket;

	len = sizeof(from);

	for (;;)
	{
		if ((client_socket = accept (m_socket, (sockaddr *)(&from), (socklen_t *)&len)) < 0) 
		{
			fprintf (stderr, "Something went wrong, what ? idk : %d\n", client_socket);
		}

		if (client_socket > 0)
		{
			std::lock_guard<std::mutex> guard_c {m_mutex};

			Client &client = RegisterClient (client_socket, {m_id_counter++, client_socket});

			std::string message = m_protocol.GetConnectionRule () ({}, client);
			Broadcast (client, message);
			fprintf (stderr, "Client [%d] joined.\n", client.GetID ());
		}
	}
}

void Server::Start ()
{
	char 				buffer [1024];
	int 				err;

	sockaddr_storage	from;
	int					len;

	time_t 				timestamp;

	int 				client_fd;
	Client 			 	*client;

	len = sizeof(from);

	if (listen (m_socket, 8) < 0)
	{
		// TODO : trow error
		throw;
	}

	std::thread listen_thread {[this]() { this->Listen (); }};

	fprintf (stderr, "Starting is now running\n");

	for (;;)
	{
		m_mutex.lock ();

		poll (m_observers.data (), m_observers.size (), 0);

		for (int i = 0; i < m_observers.size (); ++i)
		{
			client_fd 	=  m_observers [i].fd;
			client 		= &m_clients [client_fd];

			time (&timestamp);

			if (timestamp - client->GetLastActivity () >= TIMEOUT_SUS && !client->IsSuspious () && !client->IsDead ())
			{
				client->SetDeadSuspicionFlag (true);
				auto& rule = m_protocol.GetAliveRule ();
				std::string message = rule ({}, *client);
				Broadcast (*client, message);
			}

			if (CHECK_INACTIVITY && timestamp - client->GetLastActivity () >= TIMEOUT_KILL && client->IsSuspious () && !client->IsDead ())
			{
				fprintf (stderr, "Client [%d] disconnected (timeout)\n", client->GetID ());
				UnregisterClient (client_fd);
				--i; // should be fine I think (its because we swap-and-pop m_observers [i] so technically the old .back is now at index i)
				continue;
			}

			if (client->IsDead ())
			{
				fprintf (stderr, "Client [%d] disconnected (mysterious precondition)\n", client->GetID ());
				UnregisterClient (client_fd);
				--i; // should be fine I think (its because we swap-and-pop m_observers [i] so technically the old .back is now at index i)
				continue;
			}

			if (m_observers [i].revents & POLLIN)
			{
				bzero (buffer, 1024);

				if ((err = read (client_fd, buffer, sizeof (buffer))) <= 0)
				{
					if (!err)
					{
						fprintf (stderr, "Client [%d] disconnected\n", client->GetID ());
						UnregisterClient (client_fd);
						--i; // should be fine I think (its because we swap-and-pop m_observers [i] so technically the old .back is now at index i)
						continue;
					}

					fprintf (stderr, "Client [%d] disconnected : %s.\n", client->GetID (), strerror (errno));
					UnregisterClient (client_fd);
					--i;
					continue;
				}
				
				HandleClient (*client, std::string {buffer});
			}
		}
		m_mutex.unlock ();
	}
		
	listen_thread.join ();
}

void Server::Stop ()
{

}