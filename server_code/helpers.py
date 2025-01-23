from anvil import tables
from contextlib import contextmanager

import time

def _verify_column(table_columns, expected_name, expected_type):
    """Check the table has a column with the expected name and type
    Args:
        table_columns: output from app_tables.my_table.list_columns()
        expected_name: str, name of column
        expected_type: str, type of column
    """

    for column in table_columns:
        if column["name"] == expected_name:
            if column["type"] == expected_type:
                return ""
            else:
                return f"column '{expected_name}' must be of type '{expected_type}' not '{column['type']}'"
    return f"column '{expected_name}' not found"


def verify_table(table_name: str, expected_columns: dict):
    """Verify the table has all of the expected columns
    Args:
        table: str, name of table
        expected_columns: [{'name': row_name, 'type': row_type}, ...]
            Grab this from the console with app_tables.my_table.list_columns()

    Returns: List of human readable errors
        if the list is empty, no errors were found.
    """
    from anvil.tables import app_tables
    
    
    if table_name not in app_tables:
        return f"Table '{table_name}' not found."

    table = app_tables[table_name]
    
    table_columns = table.list_columns()
    errors = list()
    for column in expected_columns:
        result = _verify_column(table_columns, column["name"], column["type"])
        if result:
            errors.append(result)

    if errors:
        return errors

    return False


@tables.in_transaction
@contextmanager
def temp_row(table, **kwargs):
    """Create a temporary row in table that will be automatically deleted
    Args:
        table: app_table to create row within
        kwargs: row properties, ie. id=1234, name='john'

    Example:
        with temp_row(my_table, id=1234, name='john') as row:
            result = test_function(row)
            assert result == True, 'Some description of what is wrong and expected'

        # Once you exit the with block the row will be deleted
        row.get_id() <- This will raise a RowDeleted exception!
    """
    row = table.add_row(**kwargs)
    try:
        yield row
    finally:
        # delete our temporary row
        try:
            row.delete()
        except tables.RowDeleted:
            pass


@tables.in_transaction
@contextmanager
def temp_changes():
    """Create a temporary row in table that will be automatically deleted
    Args:
        table: app_table to create row within
        kwargs: row properties, ie. id=1234, name='john'

    Example:
        row = app_tables.my_table.add_row(key='existing_row', info='Initial Info')
        with temp_changes():
            new_row = app_tables.my_table.add_row(key='test')
            row = app_tables.my_table.get(key='existing_row')
            row['info'] = 'Changed Info'
            
        assert row['info'] == "Initial Info"

        with helpers.raises(tables.RowDeleted):
            new_row.get_id()
    """
    
    with tables.Transaction() as txn:
        try:
            yield None
        finally:
            # abort the transaction changes
            txn.abort()


@contextmanager
def raises(expected_error, msg: str | None=None):
    """ Check that a test raises a specific exception 
    Args:
        expected_error: Exception that should be raised

    Example:
    with raises(AttributeError):
        my_function()
    """
    
    try:
        yield
        assert False, msg or f"{expected_error} not raised."

    except expected_error:
        # This is the expected path...
        # Kinda silly to put this here since it does nothing.
        # But it somehow feels right.
        assert True, f"{expected_error} raised as expected."

    except AssertionError as e:
        # capture our own assertion or reraise if it was not from us.
        if str(e) != f"{expected_error} not raised.":
            raise e
        
    except Exception as e:
        # We got an exception but we didn't expect it.
        assert False, f"{type(e).__name__} raised, expected {expected_error.__name__}"
            
    finally:
        pass


def gen_int(n: int=19) -> int:
    """ Create a random int for testint"""
    v = time.time_ns() + int(str(time.time_ns())[::-1])
    if n == 19:
        return v
    return v % int(n*'9')

    
def gen_str(n: int=16) -> str:
    """ Create a random string for testing """
    return hex(gen_int())[2:n+2]