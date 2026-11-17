#pragma once
#include <QMainWindow>
#include <QStringList>
namespace Ui { class MainWindow; }
class QTableWidget;
class MainWindow : public QMainWindow {
 Q_OBJECT
public: explicit MainWindow(QWidget *parent=nullptr); ~MainWindow();
private: Ui::MainWindow *ui; QTableWidget *table; void refresh(); void run(const QStringList &args,bool reload=true); void screenshot(); QString selected() const;
};
