
#include "headers/server.hpp"
#include "headers/protocol.hpp"
#include "headers/utils.hpp"

#include <algorithm>
#include <ctime>
#include <sstream>

#define MAX_CLIENTS_ROOM 10

int main (int argc, char **argv)
{
	char* port = nullptr;
	const char* default_port = "12345";

	if (argc == 2) port = argv [1];
	else port = (char *) default_port;

	std::unordered_map <std::string, std::vector <Client *>> rooms;
	std::unordered_map <std::string, Client *> usernames;
	Server server {port};

	Protocol protocol {
		[] (std::vector<std::string> args, Client &client) -> std::string {
			return ("ERROR 11");
		},
		[&usernames, &rooms, &server] (std::vector<std::string> args, Client &client) -> std::string {
			std::string message = args [0];
			std::vector<std::string> context = client.GetTalkingContext ();

			if (context [0] == "speak")
			{
				if (rooms.find (context [1]) == rooms.end ()) return ("ERROR 31");

				auto& clients = rooms [context [1]];
	
				client.TalkToBuffer (message);
				if (message == ".")
				{
					message = client.GetTalk ();
					client.StopTalking ();
					
					trim (message);
					if (message == "") return ("ERROR 10"); // arguments invalides (message vide)

					time_t timestamp;
					time (&timestamp);

					std::string answer;
					answer = "SPEAK " + client.GetUserName () + " " + context [1] + " " + std::to_string (timestamp) + "\n" + message + "\n";
					for (auto& c : clients)
					{
						if (!c) continue;

						server.Broadcast (*c, answer);
					}
				}
			}

			else if (context [0] == "msgpv")
			{
				Client *other = usernames [context [1]];
	
				client.TalkToBuffer (message);
				if (message == ".")
				{
					message = client.GetTalk ();
					client.StopTalking ();
					
					if (message == "") return ("ERROR 10"); // arguments invalides (message vide)

					time_t timestamp;
					time (&timestamp);

					std::string answer;
					answer = "MSGPV " + client.GetUserName () + " " + std::to_string (timestamp) + "\n" + message + "\n";

					server.Broadcast (*other, answer);
				}
			}
			return ("");
		},
		[] (std::vector<std::string> args, Client &client) -> std::string {
			return ("ALIVE");
		},
		[] (std::vector<std::string> args, Client &client) -> std::string {
			return ("TCHAT 1");
		},
		[&usernames, &rooms, &server] (std::vector<std::string> args, Client &client) -> std::string {
			if (!client.IsLoggedIn ()) return ("");
			usernames.erase (client.GetUserName ());
			std::vector<Client *>::iterator pos;
			for (auto& room : rooms)
			{
				if ((pos = std::find (room.second.begin (), room.second.end (), &client)) != room.second.end ())
				{
					time_t timestamp;
					time (&timestamp);

					(*pos) = nullptr;

					std::string answer;
					answer = "LEAVE " + room.first + " " + client.GetUserName () + " " + std::to_string (timestamp);

					for (auto& c : room.second)
					{
						if (!c) continue;
						server.Broadcast (*c, answer);
					}
				}
			}
			return ("");
		}
	};

	protocol.RegisterRule ("LOGIN", [&usernames](std::vector<std::string> args, Client &client) -> std::string {
		if (args.size () != 2) return ("ERROR 10"); // arguments invalides

		std::string username = args [1];

		if (!is_string_valid (username)) return ("ERROR 20"); // pseudo invalide

		if (usernames.find (username) != usernames.end ()) return ("ERROR 23"); // pseudo déjà pris

		if (!client.IsLoggedIn ()) usernames.insert ({username, &client});
		else
		{
			usernames.erase (client.GetUserName ());
			usernames.insert ({username, &client});
		}

		client.AcceptLogin (username);

		return ("OKAY!");
	});

	protocol.RegisterRule ("ENTER", [&rooms, &server](std::vector<std::string> args, Client &client) -> std::string {
		if (!client.IsLoggedIn ()) return ("ERROR 01"); // identification nécessaire
		if (args.size () != 2) return ("ERROR 10"); // arguments invalides

		std::string room_name = args [1];

		if (rooms.find (room_name) == rooms.end ()) return ("ERROR 31"); // groupe inexistant

		auto& clients = rooms [room_name];
		
		if (clients.size () == MAX_CLIENTS_ROOM) return ("ERROR 36"); // groupe plein
		
		if (std::find (clients.begin (), clients.end (), &client) != clients.end ()) return ("ERROR 35"); // déjà dans le groupe
		
		rooms [room_name].push_back (&client);

		time_t timestamp;
		time (&timestamp);
		
		std::string answer;
		answer = "ENTER " + room_name + " " + client.GetUserName () + " " + std::to_string (timestamp);

		for (auto& c : clients)
		{
			if (!c) continue;
			server.Broadcast (*c, answer);
		}

		return ("OKAY!");
	});

	protocol.RegisterRule ("LEAVE", [&rooms, &server](std::vector<std::string> args, Client &client) -> std::string {
		if (!client.IsLoggedIn ()) return ("ERROR 01"); // identification nécessaire
		if (args.size () != 2) return ("ERROR 10"); // arguments invalides

		std::string room_name = args [1];

		if (rooms.find (room_name) == rooms.end ()) return ("ERROR 31"); // groupe inexistant

		auto& clients = rooms [room_name];
		std::vector<Client *>::iterator pos;

		if ((pos = std::find (clients.begin (), clients.end (), &client)) == clients.end ()) return ("ERROR 34"); // pas dans le groupe
		
		(*pos) = nullptr;

		time_t timestamp;
		time (&timestamp);

		std::string answer;
		answer = "LEAVE " + room_name + " " + client.GetUserName () + " " + std::to_string (timestamp);

		for (auto& c : clients)
		{
			if (!c) continue;
			server.Broadcast (*c, answer);
		}

		return ("OKAY!");
	});

	protocol.RegisterRule ("LSMEM", [&rooms, &server](std::vector<std::string> args, Client &client) -> std::string {
		if (!client.IsLoggedIn ()) return ("ERROR 01"); // identification nécessaire
		if (args.size () != 2) return ("ERROR 10"); // arguments invalides

		std::string room_name = args [1];

		if (rooms.find (room_name) == rooms.end ()) return ("ERROR 31"); // groupe inexistant

		auto& clients = rooms [room_name];

		if (std::find (clients.begin (), clients.end (), &client) == clients.end ()) return ("ERROR 34"); // pas dans le groupe

		int i = 0;
		for (auto& c : clients)
		{
			if (!c) continue;
			++i;
		}

		std::string answer;
		answer = "LSEM " + room_name + " " + std::to_string (i);
		server.Broadcast (client, answer);

		for (auto& c : clients)
		{
			if (!c) continue;
			server.Broadcast (client, c->GetUserName ());
		}

		return ("");
	});

	protocol.RegisterRule ("CREAT", [&rooms](std::vector<std::string> args, Client &client) -> std::string {
		if (!client.IsLoggedIn ()) return ("ERROR 01"); // identification nécessaire
		if (args.size () != 2) return ("ERROR 10"); // arguments invalides

		std::string room_name = args [1];

		if (!is_string_valid (room_name)) return ("ERROR 30"); // nom de groupe invalide

		if (rooms.find (room_name) != rooms.end ()) return ("ERROR 33"); // groupe existant

		rooms.insert ({room_name, std::vector <Client *>{MAX_CLIENTS_ROOM}});
		rooms [room_name].emplace (rooms [room_name].begin (), &client);

		return ("OKAY!");
	});

	protocol.RegisterRule ("SPEAK", [&rooms, &server](std::vector<std::string> args, Client &client) -> std::string {
		if (!client.IsLoggedIn ()) return ("ERROR 01"); // identification nécessaire
		if (args.size () != 2) return ("ERROR 10"); // arguments invalides

		std::string room_name = args [1];

		if (rooms.find (room_name) == rooms.end ()) return ("ERROR 31"); // groupe inexistant

		auto& clients = rooms [room_name];

		if (std::find (clients.begin (), clients.end (), &client) == clients.end ()) return ("ERROR 34"); // pas dans le groupe

		client.StartTalking ({"speak", room_name});

		return ("");
	});

	protocol.RegisterRule ("MSGPV", [&usernames, &server](std::vector<std::string> args, Client &client) -> std::string {
		if (!client.IsLoggedIn ()) return ("ERROR 01"); // identification nécessaire
		if (args.size () != 2) return ("ERROR 10"); // arguments invalides

		std::string other_username = args [1];
		if (usernames.find (other_username) == usernames.end ()) return ("ERROR 21"); // pseudo inexistant

		client.StartTalking ({"msgpv", other_username});

		return ("");
	});
	
	protocol.RegisterRule ("ALIVE", [&server](std::vector<std::string> args, Client &client) -> std::string {
		if (args.size () != 1) return ("ERROR 10"); // arguments invalides

		if (!client.IsSuspious ()) return ("");

		client.SetDeadSuspicionFlag (false);

		return ("");
	});

	server.SetProtocol (protocol);

	server.Start ();
}