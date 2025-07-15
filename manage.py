import os
import sys

if __name__ == '__main__':
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'oneSource.settings')
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc

    if len(sys.argv) > 1 and sys.argv[1] == 'runserver' and len(sys.argv) == 2:
        sys.argv.append('192.168.1.253:55')  # Specify your IP and port here

    execute_from_command_line(sys.argv)