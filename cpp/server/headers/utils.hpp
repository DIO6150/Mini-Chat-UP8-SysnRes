#pragma once

#include <string>
#include <algorithm>
#include <cctype>
#include <locale>


/*
    Thanks to https://stackoverflow.com/a/217605 for this trim function
    trim from start (in place)
*/
inline void ltrim(std::string &s) {
    s.erase(s.begin(), std::find_if(s.begin(), s.end(), [](unsigned char ch) {
        return !std::isspace(ch);
    }));
}

/*
    Thanks to https://stackoverflow.com/a/217605 for this trim function
    trim from end (in place)
*/
inline void rtrim(std::string &s) {
    s.erase(std::find_if(s.rbegin(), s.rend(), [](unsigned char ch) {
        return !std::isspace(ch);
    }).base(), s.end());
}


/*
    Thanks to https://stackoverflow.com/a/217605 for this trim function
    trim from both ends (in place)
*/
inline void trim(std::string &s) {
    rtrim(s);
    ltrim(s);
}

// trim from start (copying)
inline std::string ltrim_copy(std::string s) {
    ltrim(s);
    return s;
}

/*
    Thanks to https://stackoverflow.com/a/217605 for this trim function
    trim from end (copying)
*/
inline std::string rtrim_copy(std::string s) {
    rtrim(s);
    return s;
}

/*
    Thanks to https://stackoverflow.com/a/217605 for this trim function
    trim from both ends (copying)
*/
inline std::string trim_copy(std::string s) {
    trim(s);
    return s;
}


inline bool is_string_valid (std::string s)
{
    if (s.length () < 1 || s.length () > 16) return (false);

    std::string valid_chars = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-";

    for (auto& c : s)
    {
        if (std::find (valid_chars.begin (), valid_chars.end (), c) == valid_chars.end ()) return (false);
    }

    return (true);
}


/*
    Thanks to https://stackoverflow.com/a/14266139 for the split function
*/
inline std::vector<std::string> split (std::string s, const std::string& delimiter) {
    std::vector<std::string> tokens;
    size_t pos = 0;
    std::string token;

    while ((pos = s.find(delimiter)) != std::string::npos)
    {
        token = trim_copy (s.substr(0, pos));
        if (token != "") tokens.push_back(token);
        s.erase(0, pos + delimiter.length());
    }

    std::string t = trim_copy (s);
    if (t != "") tokens.push_back (t);

    return (tokens);
}