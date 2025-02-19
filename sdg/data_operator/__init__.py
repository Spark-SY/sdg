"""Package for data operators.

Import this package would import all modules in the package to register all
operators.
"""
import pkgutil
import importlib

package_name = __name__
package_path = __path__

for _, module_name, _ in pkgutil.iter_modules(package_path):
    full_module_name = f"{package_name}.{module_name}"
    importlib.import_module(full_module_name)
