from flask import Flask, request
from google.cloud import datastore
import datetime
import uuid
from typing import Optional, List, Dict, Any

app = Flask(__name__)
client = datastore.Client()


# --- Helpers ---

def update_var(name: str, value: Optional[str]) -> None:
    """Updates or deletes a variable in Datastore with audit metadata."""
    key = client.key('Variable', name)
    if value is None:
        client.delete(key)
    else:
        entity = datastore.Entity(key=key)
        entity.update({
            'value': value,
            'updated_at': datetime.datetime.utcnow().isoformat()  # Improvement: Audit trail
        })
        client.put(entity)


def get_history() -> datastore.Entity:
    """Fetches the global history entity, creating it if it doesn't exist."""
    key = client.key('History', 'global_state')
    hist = client.get(key)
    if not hist:
        # exclude_from_indexes ensures we stay O(1) for large history stacks
        hist = datastore.Entity(key=key, exclude_from_indexes=('undo', 'redo'))
        hist.update({'undo': [], 'redo': []})
    return hist


# --- Routes ---

@app.route('/')
def hello() -> str:
    return 'Hello, World!'


@app.route('/set')
def set_val() -> str:
    name: Optional[str] = request.args.get('name')
    value: Optional[str] = request.args.get('value')

    if not name or value is None:
        return "INVALID INPUT"

    request_id: str = str(uuid.uuid4())[:8]

    var_key = client.key('Variable', name)
    old_ent = client.get(var_key)
    old_val: Optional[str] = old_ent['value'] if old_ent else None

    update_var(name, value)

    hist = get_history()
    hist['undo'].append({
        'action': 'SET',
        'name': name,
        'prev': old_val,
        'curr': value,
        'tx_id': request_id
    })
    hist['redo'] = []
    client.put(hist)
    return f"{name} = {value}"


@app.route('/get')
def get_val() -> str:
    name: Optional[str] = request.args.get('name')
    if not name: return "None"

    key = client.key('Variable', name)
    ent = client.get(key)
    return str(ent['value']) if ent else "None"


@app.route('/unset')
def unset_val() -> str:
    name: Optional[str] = request.args.get('name')
    if not name: return "INVALID INPUT"

    var_key = client.key('Variable', name)
    old_ent = client.get(var_key)

    if not old_ent:
        return f"{name} = None"

    old_val: str = old_ent['value']
    update_var(name, None)

    request_id: str = str(uuid.uuid4())[:8]
    hist = get_history()
    hist['undo'].append({
        'action': 'UNSET',
        'name': name,
        'prev': old_val,
        'curr': None,
        'tx_id': request_id
    })
    hist['redo'] = []
    client.put(hist)
    return f"{name} = None"


@app.route('/numequalto')
def num_equal() -> str:
    val: Optional[str] = request.args.get('value')
    if val is None: return "0"

    query = client.query(kind='Variable')
    query.add_filter('value', '=', val)
    # Using keys_only=True if we just need the count for better performance
    count: int = len(list(query.fetch()))
    return str(count)


@app.route('/undo')
def undo() -> str:
    hist = get_history()
    undo_stack: List[Dict[str, Any]] = hist.get('undo', [])

    if not undo_stack:
        return "NO COMMANDS"

    last_action = undo_stack.pop()
    update_var(last_action['name'], last_action['prev'])

    redo_stack: List[Dict[str, Any]] = hist.get('redo', [])
    redo_stack.append(last_action)

    hist.update({'undo': undo_stack, 'redo': redo_stack})
    client.put(hist)

    val_display = last_action['prev'] if last_action['prev'] is not None else 'None'
    return f"{last_action['name']} = {val_display}"


@app.route('/redo')
def redo() -> str:
    hist = get_history()
    redo_stack: List[Dict[str, Any]] = hist.get('redo', [])

    if not redo_stack:
        return "NO COMMANDS"

    last_undone = redo_stack.pop()
    update_var(last_undone['name'], last_undone['curr'])

    undo_stack: List[Dict[str, Any]] = hist.get('undo', [])
    undo_stack.append(last_undone)

    hist.update({'undo': undo_stack, 'redo': redo_stack})
    client.put(hist)

    val_display = last_undone['curr'] if last_undone['curr'] is not None else 'None'
    return f"{last_undone['name']} = {val_display}"


@app.route('/end')
def end() -> str:
    # Batch deletion for efficiency
    for kind in ['Variable', 'History']:
        query = client.query(kind=kind)
        keys = [e.key for e in query.fetch()]
        if keys:
            client.delete_multi(keys)
    return "CLEANED"


if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8080, debug=True)