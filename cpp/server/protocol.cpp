#include "protocol.hpp"

#include "utils.hpp"

Protocol::Protocol ()
{
    // GRRR why can't I declare and not initialize something
}

Protocol::Protocol (
    REQUEST_CALLBACK unkown_command,
    REQUEST_CALLBACK talk_callback,
    REQUEST_CALLBACK alive_callback,
    REQUEST_CALLBACK connection_callback,
    REQUEST_CALLBACK disconnection_callback) : 
m_unkown_command_callback (unkown_command),
m_talk_callback (talk_callback),
m_alive_callback (alive_callback),
m_connection_callback (connection_callback),
m_disconnection_callback (disconnection_callback)
{

}

void Protocol::RegisterRule (std::string name, REQUEST_CALLBACK callback)
{
    if (!m_requests_callbacks.insert ({name, callback}).second)
    {
        fprintf (stderr, "Couldn't register server protocol rule.");
        return;
    }
}

REQUEST_CALLBACK &Protocol::GetRule (std::string name)
{
    std::unordered_map<std::string, REQUEST_CALLBACK>::iterator pos;
    if ((pos = m_requests_callbacks.find (name)) == m_requests_callbacks.end ()) return (m_unkown_command_callback);
    return (pos->second);
}

REQUEST_CALLBACK &Protocol::GetTalkRule ()
{
    return (m_talk_callback);
}

REQUEST_CALLBACK &Protocol::GetAliveRule ()
{
    return (m_alive_callback);
}

REQUEST_CALLBACK &Protocol::GetConnectionRule ()
{
    return (m_connection_callback);
}

REQUEST_CALLBACK &Protocol::GetDisconnectionRule ()
{
    return (m_disconnection_callback);
}


std::vector<std::string> Protocol::GetTokens (std::string message)
{
    return (split (message, " "));
}
