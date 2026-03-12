import sys

from PyQt6.QtCore import QCoreApplication, Qt
QCoreApplication.setAttribute(Qt.ApplicationAttribute.AA_ShareOpenGLContexts)
from PyQt6.QtWidgets import QApplication

from bootstrap.single_instance import ensure_single_instance
from bootstrap.startup import create_application_context


def main() -> int:
    ensure_single_instance(sys.argv)

    app = QApplication(sys.argv)
    context = create_application_context(app)
    context.main_window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())