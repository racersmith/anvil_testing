import anvil.tables as tables
from anvil.tables import app_tables

from .. import helpers


class Test_VerifyColumn:
    def test_good_column(self):
        table = app_tables.test_table

        result = helpers._verify_column(table.list_columns(), "text_col", "string")
        assert result == "", f"This is a valid column but got error: {result}"

    def test_bad_type_column(self):
        table = app_tables.test_table

        result = helpers._verify_column(table.list_columns(), "text_col", "number")
        assert (
            "type" in result and "string" in result and "number" in result
        ), f"Should get a type error: {result}"

    def test_bad_name_column(self):
        table = app_tables.test_table
        result = helpers._verify_column(
            table.list_columns(), "non_existant_column", "string"
        )
        assert (
            "not found" in result and "non_existant_column" in result
        ), f"Should get a not found error: {result}"


class TestVerifyTable:
    def __init__(self):
        self.table_name = "test_table"
        self.expected_columns = app_tables[self.table_name].list_columns()

    def test_good_table(self):
        result = helpers.verify_table(self.table_name, self.expected_columns)
        assert not result, f"Should not get errors: {result}"

    def test_bad_table_name(self):
        bad_table_name = "bad_table_name"
        result = helpers.verify_table(bad_table_name, self.expected_columns)
        assert (
            "not found" in result and bad_table_name in result
        ), f"Should get a table not found error: {result}"

    def test_bad_table_column_name(self):
        bad_columns = [{"name": "non_existant_row", "type": "string"}]
        result = helpers.verify_table(self.table_name, bad_columns)
        assert (
            "not found" in result and "non_existant_row" in result
        ), f"Should get a column not found error: {result}"

    def test_bad_table_column_type(self):
        bad_columns = [dict(self.expected_columns[0])]
        bad_columns[0]['type'] = 'bad_type'
        result = helpers.verify_table(self.table_name, bad_columns)
        assert (
            "type" in result and "bad_type" in result
        ), f"Should get a column type error: {result}"


class TestTempRow:
    def __init__(self):
        self.table = app_tables.test_table
        self.column_names = [column['name'] for column in self.table.list_columns()]

    def test_row_instance(self):
        with helpers.temp_row(app_tables.test_table) as row:
            assert isinstance(row, tables.Row), f"row is not an instance of tables.Row but {type(row)}"
            assert set('[,]').issubset(row.get_id()), f"Didn't get an expected row id: {row.get_id()}"

    def test_row_deleted_normal(self):
        with helpers.temp_row(app_tables.test_table) as row:
            row.get_id()
            
        with helpers.raises(tables.RowDeleted):
            row.get_id()

    def test_row_deleted_with_exception(self):
        with helpers.raises(KeyboardInterrupt):
            with helpers.temp_row(app_tables.test_table) as row:
                row.get_id()
                raise KeyboardInterrupt('Testing the exception does not keep the row alive')
                    
        with helpers.raises(tables.RowDeleted):
            row.get_id()
    
    def test_empty_row(self):
        with helpers.temp_row(app_tables.test_table) as row:
            for column in self.column_names:
                assert column in row, f"row should have column: '{column}'"
                assert row[column] is None, f"row[{column}] should be None"
                        
        with helpers.raises(tables.RowDeleted):
            row.get_id()

    def test_populated_row(self):
        expected_data = {'text_col': 'abc', 'number_col': 1234, 'bool_col': True}
        with helpers.temp_row(app_tables.test_table, **expected_data) as row:
            for column in self.column_names:
                assert row[column] == expected_data[column], f"row[{column}] = {row[column]} expected {expected_data[column]}"
                
    def test_with_existing_rows(self):
        with helpers.temp_row(app_tables.test_table, text_col='row_a') as existing_row:
            existing_frozen = dict(existing_row)
            with helpers.temp_row(app_tables.test_table, text_col='row_b') as new_row:
                rows = self.table.search()
                assert len(rows) == 2, f"Expected to have two rows"
                new_row['bool_col'] = True
                assert dict(existing_row) == existing_frozen, f"existing row somehow changed!"

    def test_deleted(self):
        try:
            with helpers.temp_row(app_tables.test_table, text_col='row_a') as row:
                row.delete()
        except Exception as e:
            assert False, f"Error after deleting row within block: {e}"


class TestRaises:
    def test_expected(self):
        try:
            with helpers.raises(ValueError):
                raise ValueError('Just a test exceptioon')
            assert True, "ValueError was captured"
        except AssertionError as e:
            assert False, f"Should not be raising an AssertionError: {e}"

    def test_unexpected(self):
        try:
            with helpers.raises(LookupError):
                raise ValueError('Just a test exceptioon')
            assert False, "ValueError was incorrectly captured"
        except AssertionError as e:
            assert 'ValueError raised' in str(e), f"Wrong assertion error: {e}"
            assert 'expected LookupError' in str(e), f"Wrong assertion error: {e}"

    def test_no_exception(self):
        try:
            with helpers.raises(LookupError):
                pass
        except AssertionError as e:
            assert 'LookupError not raised' in str(e), f"Expected to get a not raised assertion: {e}"
            
            