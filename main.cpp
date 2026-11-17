#include <QApplication>
#include "mainwindow.h"
int main(int argc,char **argv) { QApplication app(argc,argv); app.setApplicationName("eventorix-public"); app.setApplicationVersion("0.1.1"); MainWindow w; w.show(); return app.exec(); }
