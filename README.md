# phable
Manage Phabricator tasks from the comfort of your terminal.

`phable` is a CLI allowing you to manage your [Phorge/Phabricator](https://we.phorge.it) tasks.

It tries to be very simple and not go overboard with features. You can:
- create a new task
- display a task details
- move a task to a column on its current board
- assign a task to a user
- add a comment to a task
- and more (see `phable --help` output for the full feature list)

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
  assign             Assign one or multiple task ids to a username
  cache              Manage internal cache
  comment            Add a comment to a task
  config             Manage phable config
  create             Create a new task
  list               Lists and filter tasks
  move               Move one or several task on their current project board
  parent             Manage task parents
  report-done-tasks  Print the details of all tasks in the `from` column and move them to the `to` column.
  show               Show task details
  status             Set the status of one or multiple tasks
  subscribe          Subscribe to one or multiple task ids
  tag                Add a tag on one or multiple tasks
```

## Setup

For `phable` to work, you need to define the following configuration, by running `$EDITOR $(phable config show)`:

```ini
[phabricator]
url = # URL to your phabricator instance. Ex: `url = https://phabricator.wikimedia.org`
token = # API token. Generate a token from ${PHABRICATOR_URL}/settings/user/${YOUR_USERNAME}/page/apitokens/
default_project_phid = # id for the Phabricator project to be used by default when creating tasks.
```

To get `default_project_phid`, define the first 2 configurations, and run the following command, where `T123456` is a task id belonging to your project.

```console
$ phable show T123456 --format=json | jq -r '.attachments.projects.projectPHIDs[]'
```

Note: you can also expose these configuration through the following environment variables, for backwards compatibility:
- `PHABRICATOR_URL`
- `PHABRICATOR_TOKEN`
- `PHABRICATOR_DEFAULT_PROJECT_PHID`

## Tips and tricks

### Setting up aliases
You can define command aliases. For example, instead of typing `phable move --column 'Done' --milestone T123456`, you might want to type `phable done T123456`. To do this, open the phable configuration file, with `$EDITOR $(phable config show)` and define an alias:

```ini
[aliases]
done = move --column 'Done' --milestone
```

I personally currently have the following aliases:
```console
$ phable config aliases list
done = move --column 'Done' --milestone
review = move --column 'Needs Review' --milestone
wip = move --column 'In Progress' --milestone
team-report = list --owner brouberol --column 'In Progress' --column 'Needs Review' --column 'Blocked/Waiting' --column Done --milestone --format html
```

### Phabricator task IDs as clickable links in iTerm2
If you're using iTerm2, you can turn the task IDs into clickable links, by going to iTerm2 > Settings > Profiles > Advanced > Smart Selection > Edit > [+]:
- Title: Phabricator Task Id
- Action: Open URL
- Parameter: https://phabricator.wikimedia.org/\0 (Adjust your Phabricator URL)

Then click on the new rule Notes field, and set it to Phabricator, and set the Regular expression field to `T\d{6}` (adjust the number of digits to what a task ID looks like in your instance. The latest created task has ID 385678 right now, so `\d{6}` gives us some leeway).

One that is done, holding `Command` when hovering on a task ID should turn it into a link.

### Enabling autocompletion

#### bash

Add this to `~/.bashrc`:
```
eval "$(_PHABLE_COMPLETE=bash_source phable)"
```

#### zsh

Add this to `~/.zshrc`:

```
eval "$(_PHABLE_COMPLETE=zsh_source phable)"
```

#### fish

Add this to `~/.config/fish/completions/phable.fish`:

```
_PHABLE_COMPLETE=fish_source phable | source
```
