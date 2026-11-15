# Execution Eigine Architecture & Design docs


## **Questions & Answers : **

## What is the Responsibility of Docker Manager?
- Control Docker Engine and containers lifecycle

## What is the Responsibility of Workspace Manager?
- Create isolated task directories or Git workspace

## How will we isolate one task's file from another task?
- Instead of mounting the original project directly, create a seprate task workspace 
    - Original repo -> Task workspace ( Independent working branch ) -> ( Bind mount into container ) Docker container -> (Generate  diff and validate) Human review and approval 

## What is the responsibility of Command Executor?
- Execute command in Docker container

## How will the Command Executor return execution results ?
- The command executor runs commands inside the container and collects their results 
    - **For example** 
        1. `Agent request a test run`
        2. `Command executor sends pytest to the container `
        3. `Container executes pytest`
        4. `Executor capture output and exit code`
        5. `Evalutor interprets the result`

## How will approved changes get back into the orginal respository ?
- Imagine user have project (my_project) we don't modify original project directly instead we create a seprate Git branch

    - **For example**
        - `main ----> ae/task-001`

    Agent only work on `ae/task-001` . 
- Using Git worktree we create separate working directory 
    - **For example**
        - `my_project/     -> orginal working directory`
        - `my-project-ae-task-001/ -> Agent working directory`
- Agents make changes run test fix bugs 
- `Generate Git diff` : Git can tell us what changes have been made compare to the original branch
- **Human review and approval :** User can see diff 
    - Accept : Changes will merge in orignal branch
    - Reject : Task branch will be discard
    - Req changes : Give agent feedback and request changes