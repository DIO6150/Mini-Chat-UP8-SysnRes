#pragma once

#include <unordered_map>
#include <string>
#include <functional>

#include "client.hpp"

#define REQUEST_CALLBACK std::function<std::string (std::vector<std::string>, Client &)>

class Protocol
{
    std::unordered_map<std::string, REQUEST_CALLBACK> m_requests_callbacks;

    REQUEST_CALLBACK m_unkown_command_callback;
    REQUEST_CALLBACK m_talk_callback;
    REQUEST_CALLBACK m_alive_callback; // i'm calling this a request_callback but it isn't, in fact the server does that on its own so the polar opposite of a request

public:
    Protocol ();
    Protocol (REQUEST_CALLBACK unkown_command, REQUEST_CALLBACK talk_callback, REQUEST_CALLBACK alive_callback);

    void RegisterRule (std::string name, REQUEST_CALLBACK callback);

    REQUEST_CALLBACK &GetRule (std::string name);
    REQUEST_CALLBACK &GetTalkRule ();
    REQUEST_CALLBACK &GetAliveRule ();

    std::vector<std::string> GetTokens (std::string message);
};