# A 'easy' plan and task to check the AI and runner are actually working

We need a 'real' test of the run mode connected via Openrouter to a real AI.

This is to ensure the connection and process for a simple known plan and run of that plan is working before we try more complex and demanding plans involving files, terminals and tools.

## Goal

The pre-generates overview and steps plan (using AIWHisperer format produced normally output from a generate --full-project) we will use as our test, consist of 4 steps.

1. Pick a landmark from a list of 20 landmarks
2. Ask AI: what country is the landmark in ?
3. Wait for the reply and check its answer is correct
4. Ask AI: What is the Capitol of the Country?
5. Wait for the answer and check the answer
6. Is the landmark in the Capitol?
7. Wait for the answer and check the answer

This will show various thinsg are working in a 'real' if simple test.

1. Test the plan is executing
2. Ask AI step is sending the correct question and recieving the answer
3. Validate (Check the answer) are working
4. Check token context are working and being send to the AI over several steps
5. Check the streaming is working to OpenRouter.

This will provide us a simple benchmark test we can use anytime we need to have a reliable simple check.

## Issues to consider:
We may need to have several answers and may be free from in the response, for example if we asked the AI, 
> What Country is Big Ben In?
Accectable Correct Answers might be
1. England
2. United Kingdom
4. UK, U.K.
3. Great Britain.
4. Big Ben is in London in the England.