import inspect as _inspect

FN_PREFIX = "test_"
CLS_PREFIX = "Test"


def _find_tests(x):
    """recursivly find all functions/methods within the module that start with the test prefix"""
    found_tests = list()

    for name in dir(x):
        if not name.startswith("_"):
            obj = getattr(x, name)

            # Delve into modules
            if _inspect.ismodule(obj):
                found_tests.extend(_find_tests(obj))

            # Extract test methods from classes
            elif _inspect.isclass(obj) and name.startswith(CLS_PREFIX):
                # this creates a common class instance for test methods

                found_tests.extend(_find_tests(obj))

            # grab test methods
            elif (
                _inspect.isclass(x)
                and _inspect.isfunction(obj)
                and name.startswith(FN_PREFIX)
            ):
                # since x is not an instance of the class obj is not seen as a method and rather, a function.

                # create a new class instance for each test method.
                class_instance = x()
                found_tests.append(getattr(class_instance, name))

            # grab test functions
            elif _inspect.isfunction(obj) and name.startswith(FN_PREFIX):
                found_tests.append(obj)

    return found_tests


def _format_test_name(fn, test_module_name="tests"):
    """Get a descriptive name of the function that explains where it lives"""
    module = fn.__module__.split(f"{test_module_name}.")[-1]
    return f"{module}.{fn.__qualname__}"


def run(test_package):
    log = list()
    log.append("== Starting Test ==")
    found_tests = _find_tests(test_package)
    n_tests = len(found_tests)
    log.append(f"Found {n_tests} tests\n")

    passed = 0
    failed = 0

    for fn in found_tests:
        test_name = _format_test_name(fn, "tests")
        try:
            fn()
            passed += 1
            log.append(f"  Pass: {test_name}")

        except AssertionError as e:
            log.append(f"> Fail: {test_name} - {e}")
            failed += 1

    log.append(f"\n{passed}/{n_tests} passed")
    log.append(f"{failed} failed tests")

    print("\n".join(log))
