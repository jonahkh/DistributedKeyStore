import json
file = open('data.json', 'w')
output = {'requests': []}
for key in range(0, 49):
    output['requests'].append({
        'operation': 'PUT',
        'key': key,
        'value': 'value'
    })
try:
    file.write(str(json.dumps(output)))
except Exception as e:
    print(e)
file.close()