# Dating App Matching Algorithm Challenge

## Overview
You are tasked with developing a matching algorithm for a dating app. The challenge consists of three tasks that progressively explore different aspects of matchmaking, from strict compatibility to nuanced matching based on user profiles.

## Server Endpoints

The server provides two endpoints:

### 1. Get Users
```
GET https://snr-eng-7c5af300401d.herokuapp.com/api/users
```
Returns a JSON response containing all users with their complete profiles. Analyze the response to understand the user profile structure and available fields.

### 2. Validate Matches
```
POST https://snr-eng-7c5af300401d.herokuapp.com/api/validate-matches
```
Submit matches for validation. Only returns true if ALL submitted matches are 100% compatible.

Request body:
```json
{
    "matches": [
        {
            "user1_id": "uuid1",
            "user2_id": "uuid2"
        }
    ]
}
```

Response:
```json
{
    "success": true/false
}
```

## Tasks

### Task 1: Perfect Matches
Develop an algorithm to identify all 100% compatible matches based on dealbreakers in user profiles. Use the validation endpoint to verify your matches.

Requirements:
- Analyze user profiles to understand what makes a perfect match
- Implement an algorithm to find these matches
- Validate your matches using the endpoint
- The order of user IDs in a match doesn't matter (user1_id/user2_id can be swapped)

### Task 2: Match Ranking
For users with multiple potential matches, create a ranking system that determines which matches are most likely to be successful based on the entire user profile.

Requirements:
- Consider all aspects of user profiles, not just dealbreakers
- Provide clear reasoning for why certain matches rank higher than others
- Document your approach to converting qualitative profile data into quantitative match rankings

### Task 3: Potential First Dates
Identify matches that might not be 100% compatible but could still lead to successful first dates based on user profiles.

Requirements:
- Analyze profiles beyond just dealbreakers
- Consider factors that might make for good first date chemistry
- Explain your reasoning for each suggested match
- Document what factors you considered and why

## Submission Requirements

Submit a GitHub repository containing at least the following files:

1. `task1.py` - Script that implements the perfect matching algorithm and validates the matches using the validation endpoint

2. `task2.txt` - Documentation of your match ranking system, including:
   - Scoring methodology
   - Factors considered
   - Example rankings with explanations
   - How you automated the ranking process

3. `task3.txt` - Analysis of potential first date matches outside of the 100% compatible matches, including:
   - Matching criteria used
   - Example matches with explanations
   - Reasoning behind your approach

### Additional Requirements

- If you used AI tools, include your chat history showing how you used them
- Comment your code and document your thought process
- Include any test cases or validation approaches you used

## Evaluation Criteria

Your solution will be evaluated based on:

1. Task 1:
   - Accuracy in finding as many of the 100% matches as possible
   - Code quality and efficiency
   - Testing approach

2. Task 2:
   - Creativity in ranking methodology
   - Depth of profile analysis
   - Feasibility of automation
   - Quality of reasoning

3. Task 3:
   - Understanding of human compatibility
   - Creativity in match suggestions
   - Quality of explanations
   - Consideration of various factors

Remember: There's no perfect answer for Tasks 2 and 3. We're interested in your approach to this complex problem, your reasoning, and how you break down and solve each component.

