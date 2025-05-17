#include "headers/client.hpp"

Client::Client (int id, int socket) :
m_id {id},
m_socket {socket},
m_logged_in {false},
m_is_talking {false},
m_talk_buffer {""},
m_talk_context {},
m_potentially_dead {false},
m_is_dead {false}
{
    time (&m_last_activity);
}

Client::Client ()
{
    
}

int Client::GetID () const
{
    return (m_id);
}

int Client::GetSocket () const
{
    return (m_socket);
}

int Client::IsLoggedIn () const
{
    return (m_logged_in);
}

void Client::AcceptLogin (std::string user_name)
{
    m_logged_in = true;
    m_user_name = user_name;
}

std::string Client::GetUserName () const
{
    return (m_user_name);
}

void Client::StartTalking (std::vector<std::string> context)
{
    m_is_talking = true;
    m_talk_context = context;
}

void Client::StopTalking ()
{
    m_is_talking = false;
    m_talk_buffer = "";
    m_talk_context.clear ();
}

bool Client::IsTalking () const
{
    return (m_is_talking);
}

void Client::TalkToBuffer (std::string message)
{
    m_talk_buffer += message + "\n";
}

std::vector<std::string> &Client::GetTalkingContext ()
{
    return (m_talk_context);
}

std::string Client::GetTalk () const
{
    return (m_talk_buffer);
}

void Client::SetDeadSuspicionFlag (bool flag)
{
    m_potentially_dead = flag;
}

bool Client::IsSuspious () const
{
    return (m_potentially_dead);
}

void Client::Kill ()
{
    m_is_dead = true;
}

bool Client::IsDead () const
{
    return (m_is_dead);
}

void Client::UpdateActivity ()
{
    time (&m_last_activity);
}

time_t Client::GetLastActivity () const
{
    return (m_last_activity);
}
