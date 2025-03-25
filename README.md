# phable
Manage Phabricator tasks from the comfort of your terminal.

`phable` is a CLI allowing you to manage your [Phorge/Phabricator](https://we.forge.it) tasks.

It tries to be very simple and not go overboard with features. You can:
- create a new task
- display a task details
- move a task to a column on its current board
- assign a task to a user
- add a comment to a task

## Installation

```console
$ pip install phable-cli
```

## Usage

```console
$ phable --help
Usage: phable [OPTIONS] COMMAND [ARGS]...

  Manage Phabricator tasks from the comfort of your terminal

Options:
  --help  Show this message and exit.

Commands:
  assign   Assign one or multiple task ids to a username
  comment  Add a comment to a task
  create   Create a new task
  move     Move one or several task on their current project board
  show     Show task details
```
