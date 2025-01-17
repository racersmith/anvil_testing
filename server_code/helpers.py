from contextlib import contextmanager
from anvil import tables


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


def verify_columns(table, expected_columns):
    """Verify the table has all of the expected columns
    Args:
        table: app_table
        expected_columns: [{'name': row_name, 'type': row_type}, ...]
            Grab this from the console with app_tables.my_table.list_columns()

    Returns: List of human readable errors
        if the list is empty, no errors were found.
    """
    table_columns = table.list_columns()
    errors = list()
    for column in expected_columns:
        result = _verify_column(table_columns, column["name"], column["type"])
        if result:
            errors.append(result)

    if errors:
        fmt = "\n\t - "
        error_block = fmt + fmt.join(errors)
        return error_block

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
        row.delete()


@contextmanager
def raises(expected_error):
    # create our temporary row
    try:
        yield
        assert False, f"{expected_error} not raised."

    except expected_error:
        assert True, f"{expected_error} raised."

    except Exception as e:
        assert False, f"{type(e).__name__} raised, expected {expected_error.__name__}"

    finally:
        pass
