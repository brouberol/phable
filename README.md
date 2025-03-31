# phable
Manage Phabricator tasks from the comfort of your terminal.

`phable` is a CLI allowing you to manage your [Phorge/Phabricator](https://we.phorge.it) tasks.

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
  --version  Show the version and exit.
  --help     Show this message and exit.

Commands:
  assign     Assign one or multiple task ids to a username
  comment    Add a comment to a task
  create     Create a new task
  move       Move one or several task on their current project board
  show       Show task details
  subscribe  Subscribe to one or multiple task ids
```

## Setup

For `phable` to work, you need to define the following environment variables:

- `PHABRICATOR_URL`: URL to your phabricator instance. Ex: `PHABRICATOR_URL=https://phabricator.wikimedia.org`
- `PHABRICATOR_TOKEN`: Generate a token from ${PHABRICATOR_URL}/settings/user/${YOUR_USERNAME}/page/apitokens/
- `PHABRICATOR_DEFAULT_PROJECT_PHID`: id for the Phabricator project to be used by default when creating tasks.

Note: to get `PHABRICATOR_DEFAULT_PROJECT_PHID`, define the first 2 environment variables, and run the following command, where T123456 is a task id belonging to your project.

```console
$ phable show T123456 --format=json | jq -r '.attachments.projects.projectPHIDs[]'
```

## Tips and tricks

If you're using iTerm2, you can turn the task IDs into clickable links, by going to iTerm2 > Settings > Profiles > Advanced > Smart Selection > Edit > [+]:
- Title: Phabricator Task Id
- Action: Open URL
- Parameter: https://phabricator.wikimedia.org/\0 (Adjust your Phabricator URL)

Then click on the new rule Notes field, and set it to Phabricator, and set the Regular expression field to `T\d{6}` (adjust the number of digits to what a task ID looks like in your instance. The latest created task has ID 385678 right now, so `\d{6}` gives us some leeway).

One that is done, holding `Command` when hovering on a task ID should turn it into a link.
