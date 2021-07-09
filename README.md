# Hasura Enforce camelCase

This Python script overwrites Hasura table configuration metadata (via the metadata API) to alias all your tables, root queries, and fields with camelCase names in GQL. This is helpful if you have snake_case tables and fields and/or you want to override Hasura's default naming of things like `_by_pk` queries.

There is an issue open for this in Hasura [here](https://github.com/hasura/graphql-engine/issues/3320) to follow their updates on a potential fix/workaround for some of the issues with default naming.

## Installation

* Ensure you have Python3 installed
* Install the required libs: `pip install pandas inflect pyhumps`
* Clone this repo and edit the Hasura connection parameters under the `# Enter Parameters Here:` comment in `apply_naming_conventions.py` file

## Running

To run, just call `python apply_naming_conventions.py` (you might need to use `python3` depending how your system is setup). You will see output regarding which tables have been changed.

This script is idempotent, so you can run it over and over again on your tables (perhaps even as a precommit with a subsequent metadata export if you like). We run this script anytime we have a change to our model in order to ensure our GQL schemas are kept up to date.

## Potential metadata loss

Since this script _overrides_ the `configuration` property in the metadata for _each_ table with the generated camelized names, you will lose any custom configuration changes to naming or aliases for a table when you run this script. To mitigate this, just modify the script with your exceptions.

## Credits

Some ideas adopted from https://github.com/m-rgba/hasura-snake-to-camel

