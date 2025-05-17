#pragma once

#include <string>
#include <vector>
#include <ctime>

class Client
{
    int                             m_id;
    int                             m_socket;

    bool                            m_logged_in;
    std::string                     m_user_name;

    bool                            m_is_talking;

    std::string                     m_talk_buffer;

    std::vector<std::string>        m_talk_context;

    bool                            m_potentially_dead;
    bool                            m_is_dead;

    time_t                          m_last_activity;

public:
    Client ();
    Client (int id, int socket);

    int GetID () const;
    int GetSocket () const;

    int IsLoggedIn () const;
    void AcceptLogin (std::string user_name);

    std::string GetUserName () const;

    void StartTalking (std::vector<std::string> context);
    void StopTalking ();
    bool IsTalking () const;
    void TalkToBuffer (std::string message);
    std::vector<std::string> &GetTalkingContext ();
    std::string GetTalk () const;
    
    void SetDeadSuspicionFlag (bool flag);
    bool IsSuspious () const;

    void Kill ();
    bool IsDead () const;

    void UpdateActivity ();
    time_t GetLastActivity () const;
};