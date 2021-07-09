import requests
import json
import pandas as pd
import humps
import inflect

# Enter Parameters Here:
hasura_hostname = 'http://localhost:8080'  # stripping the /v1/graphql, etc.
admin_secret = '<<<YOUR HASURA ADMIN SECRET>>>'
db_source = 'default'  # Your Hasura DB name (if not using default)
db_schema = 'public'  # Your Hasura DB schema (if not using public)

# Inflect word to plural / singular
p = inflect.engine()


def get_field_parts(field):
    field_decamel = humps.decamelize(field)
    # Split up words to lists
    return field_decamel.split('_')


def get_camelized(field):
    return humps.camelize(field)


def get_pluralized(field):
    words = get_field_parts(field)
    # Plural version - last word plural
    plural = p.plural_noun(words[-1])
    if plural != False:
        plural_words = words[:-1]
        plural_words.append(plural)
    else:
        plural_words = words
    return plural_words[0] + ''.join(x.title() for x in plural_words[1:])


def get_singular(field):
    words = get_field_parts(field)
    # Singular version - last word singular
    singular = p.singular_noun(words[-1])
    if singular != False:
        singular_words = words[:-1]
        singular_words.append(singular)
    else:
        singular_words = words
    return singular_words[0] + ''.join(x.title() for x in singular_words[1:])


column_names_resp = requests.post(hasura_hostname + '/v2/query',
                                  json={"type": "run_sql", "args": {"source": db_source,
                                                                    "sql": "SELECT column_name, table_name, is_generated, is_identity, identity_generation\n  FROM information_schema.columns where table_schema = '" + db_schema + "';",
                                                                    "cascade": False,
                                                                    "read_only": True}},
                                  headers={'x-hasura-admin-secret': admin_secret})
if column_names_resp.ok:
    column_data = pd.DataFrame(json.loads(column_names_resp.text)['result'])
else:
    print(column_names_resp.reason)
    raise Exception("We had trouble contacting your API -- please check your hostname.")

new_header = column_data.iloc[0]
column_data = column_data[1:]
column_data.columns = new_header

print(column_data)
table_names = column_data['table_name'].unique()
print(table_names)

for table_name in table_names:
    print('Table: ', table_name)
    table_name_p = get_pluralized(table_name)
    table_name_s = get_singular(table_name)

    # Build Object
    json_data = {}
    args = {}
    configuration = {}
    custom_root_fields = {}
    custom_column_names = {}

    # Create Custom Table Config Payload
    json_data['type'] = 'pg_set_table_customization'
    args['table'] = table_name
    args['source'] = db_source

    json_data['args'] = args
    args['configuration'] = configuration
    configuration['custom_root_fields'] = custom_root_fields
    custom_root_fields['select'] = table_name_p
    custom_root_fields['select_by_pk'] = table_name_s
    custom_root_fields['select_aggregate'] = table_name_p + 'Aggregate'
    custom_root_fields['insert'] = table_name_p + 'Insert'
    custom_root_fields['insert_one'] = table_name_s + 'Insert'
    custom_root_fields['update'] = table_name_p + 'Update'
    custom_root_fields['update_by_pk'] = table_name_s + 'Update'
    custom_root_fields['delete'] = table_name_p + 'Delete'
    custom_root_fields['delete_by_pk'] = table_name_s + 'Delete'
    configuration['custom_name'] = table_name_s
    configuration['custom_column_names'] = custom_column_names

    cols = column_data[column_data['table_name'] == table_name]['column_name']
    for v in cols:
        custom_column_names[v] = get_camelized(v)

    print(json_data)
    update_table_config = requests.post(hasura_hostname + '/v1/metadata', json=json_data,
                                        headers={'x-hasura-admin-secret': admin_secret})
    if update_table_config.ok:
        print('-----------------------------------------')
        print('Success: ' + table_name)
    else:
        print('-----------------------------------------')
        print('Failure: ' + table_name)
        print(update_table_config.reason)
