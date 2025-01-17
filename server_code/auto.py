import inspect as _inspect

FN_PREFIX = "test_"
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


def run(test_package, quiet=True):
    log = list()
    log.append(f"{' Anvil Testing ':=^50s}")
    found_tests = _find_tests(test_package)
    n_tests = len(found_tests)
    log.append(f"Found {n_tests} tests\n")

    passed = 0
    failed = 0

    for test in found_tests:
        test_name = _format_test_name(test, "tests")
        try:
            # Run the test
            test()
            passed += 1
            if not quiet:
                log.append(f"  Pass: {test_name}")

        # capture the assertion error from our test
        except AssertionError as e:
            log.append(f"> Fail: {test_name} - {e}")
            failed += 1

    # Summary info
    log.append(f"\n{passed}/{n_tests} passed")
    log.append(f"{failed} failed tests")
    result = ' PASS ' if not failed else ' FAIL '
    log.append(f"{result:=^50s}")

    # I found this more reliable for printing to the console.
    # Otherwise, printing as I went the lines would stack, get out of order, etc.

    result = "\n".join(log)
    print(result)
    return result
