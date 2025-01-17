import anvil.tables as tables
import anvil.tables.query as q
from anvil.tables import app_tables
import inspect as _inspect
from dataclasses import dataclass

FN_PREFIX = "test_"  # also the method prefix
CLS_PREFIX = "Test"


def _find_tests(parent):
    """recursivly find all functions/methods within the module that start with the test prefix"""
    found_tests = list()

    for name in dir(parent):
        if not name.startswith("_"):
            obj = getattr(parent, name)

            # Delve into modules in the same path, don't stray into imports.
            if _inspect.ismodule(obj) and obj.__name__.startswith(parent.__name__):
                found_tests.extend(_find_tests(obj))

            # Extract test methods from classes
            elif _inspect.isclass(obj) and name.startswith(CLS_PREFIX):
                found_tests.extend(_find_tests(obj))

            # grab test methods
            # since parent is not an instance of the class obj is not seen as a method and rather, a function.
            elif (
                _inspect.isclass(parent)
                and _inspect.isfunction(obj)
                and name.startswith(FN_PREFIX)
            ):
                # create a new class instance for each test method to isolate the tests
                class_instance = parent()
                found_tests.append(getattr(class_instance, name))

            # grab test functions
            elif _inspect.isfunction(obj) and name.startswith(FN_PREFIX):
                found_tests.append(obj)

    return found_tests


def _format_test_name(fn, test_module_name="tests"):
    """Get a descriptive name of the function that explains where it lives"""
    module = fn.__module__.split(f"{test_module_name}.")[-1]
    return f"{module.replace('.', '/')}::{fn.__qualname__.replace('.', '::')}"


@dataclass
class TestResult:
    success: bool
    test_name: str
    error: str = ""

    def __str__(self):
        if self.success:
            return f"  Pass: {self.test_name}"
        else:
            return f"> Fail: {self.test_name} - {self.error}"

    def __add__(self, other) -> int:
        return other + int(self.success)

    def __radd__(self, other) -> int:
        if not other:
            return int(self.success)
        else:
            return self.__add__(other)


def _run_test(test) -> TestResult:
    """Run a single test"""
    test_name = _format_test_name(test, "tests")

    try:
        # Run the test
        test()
        return TestResult(True, test_name)

    # capture the assertion error from our test
    except AssertionError as e:
        return TestResult(False, test_name, e)

    # capture a run error to aid in debugging
    # otherwise we just get the standard anvil runtime exception error.
    except Exception as e:
        return TestResult(False, test_name, f"{type(e).__name__}: {e}")


def run(test_package, quiet=True):
    """Run the test suite
    Args:
        test_package: module where the tests reside
        quiet: True will only display failed tests, False will include passing tests in results
    """
    log = list()
    log.append(f"{' Anvil Testing ':=^50s}")
    found_tests = _find_tests(test_package)
    n_tests = len(found_tests)
    log.append(f"Collected {n_tests} tests\n")

    # Run the collected tests
    test_results = [_run_test(test) for test in found_tests]

    # add results to output log
    log.extend(str(result) for result in test_results)

    # Summary info
    passed = sum(test_results)
    failed = n_tests - passed
    log.append(f"\n{passed}/{n_tests} passed")
    log.append(f"{failed} failed tests")
    result = " PASS " if not failed else " FAIL "
    log.append(f"{result:=^50s}")

    # I found this more reliable for printing to the console.
    # Otherwise, printing as I went the lines would stack, get out of order, etc.
    result = "\n".join(log)
    print(result)
    return result
