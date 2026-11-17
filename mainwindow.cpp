#include "mainwindow.h"
#include "ui_mainwindow.h"
#include <QTableWidget>
#include <QHeaderView>
#include <QPushButton>
#include <QHBoxLayout>
#include <QInputDialog>
#include <QLineEdit>
#include <QProcess>
#include <QJsonDocument>
#include <QJsonArray>
#include <QJsonObject>
#include <QDateTime>
#include <QDir>
#include <QStandardPaths>
#include <QPixmap>
#include <QPainter>
#include <QUuid>
#include <QTimer>
#include <QDebug>
#include <QCoreApplication>
#include <QStatusBar>
MainWindow::MainWindow(QWidget *parent):QMainWindow(parent),ui(new Ui::MainWindow){
 ui->setupUi(this); table=new QTableWidget(0,5,this); table->setHorizontalHeaderLabels({"Source","Message","Assigned","Due (local)","Status"}); table->horizontalHeader()->setSectionResizeMode(1,QHeaderView::Stretch); table->setSelectionBehavior(QAbstractItemView::SelectRows); table->setEditTriggers(QAbstractItemView::NoEditTriggers); ui->verticalLayout->addWidget(table);
 auto *bar=new QHBoxLayout; ui->verticalLayout->addLayout(bar);
 auto button=[&](QString name,auto callback){auto *b=new QPushButton(name,this);bar->addWidget(b);connect(b,&QPushButton::clicked,this,callback);};
 button("Refresh",[this]{refresh();}); button("Schedule",[this]{bool ok=false;auto msg=QInputDialog::getText(this,"Schedule","Message",QLineEdit::Normal,{},&ok); if(!ok||msg.isEmpty())return; auto delay=QInputDialog::getText(this,"Schedule","Delay (5m, 14d)",QLineEdit::Normal,"5m",&ok);if(ok)run({"schedule","--source","EventorixMonitor","--assigned-to","all","--after",delay,"--message",msg});});
 button("Edit",[this]{auto id=selected();if(id.isEmpty())return;bool ok;auto msg=QInputDialog::getText(this,"Edit","Message",QLineEdit::Normal,{},&ok);if(ok)run({"update","--id",id,"--message",msg});});
 button("Delete",[this]{auto id=selected();if(!id.isEmpty())run({"delete","--id",id});}); button("Restore",[this]{auto id=selected();if(!id.isEmpty())run({"restore","--id",id});}); bar->addStretch(); button("Screenshot",[this]{screenshot();});
 ui->statusbar->showMessage("Eventorix Public | 0.1.1"); refresh();
}
MainWindow::~MainWindow(){delete ui;}
QString MainWindow::selected() const {auto *item=table->item(table->currentRow(),0);return item?item->data(Qt::UserRole).toString():QString();}
void MainWindow::refresh(){run({"list","--include-deleted"},false);}
void MainWindow::run(const QStringList &args,bool reload){auto *p=new QProcess(this); auto cli=QCoreApplication::applicationDirPath()+"/eventorix"; connect(p,&QProcess::errorOccurred,this,[this,p](QProcess::ProcessError){ui->statusbar->showMessage(p->errorString());p->deleteLater();});connect(p,qOverload<int,QProcess::ExitStatus>(&QProcess::finished),this,[this,p,args,reload](int code,QProcess::ExitStatus status){auto out=p->readAllStandardOutput();auto err=p->readAllStandardError();p->deleteLater();if(code||status!=QProcess::NormalExit){ui->statusbar->showMessage(QString::fromUtf8(err));return;}if(args.first()=="list"){auto rows=QJsonDocument::fromJson(out).array();table->setRowCount(0);for(auto value:rows){auto r=value.toObject();int i=table->rowCount();table->insertRow(i);QStringList fields={r["source"].toString(),r["message"].toString(),r["assigned_to"].toString(),QDateTime::fromSecsSinceEpoch(r["due_at"].toVariant().toLongLong()).toString(Qt::ISODate),r["status"].toString()};for(int j=0;j<fields.size();++j)table->setItem(i,j,new QTableWidgetItem(fields[j]));table->item(i,0)->setData(Qt::UserRole,r["id"].toString());}}ui->statusbar->showMessage("Operation completed");if(reload)refresh();});p->start(cli,args);}
void MainWindow::screenshot(){
    const auto dir=QStandardPaths::writableLocation(QStandardPaths::AppDataLocation)+"/screenshots";
    if(!QDir().mkpath(dir)){qWarning()<<"Screenshot directory failed";return;}
    const auto file=dir+"/eventorix-public-0.1.1-"+QDateTime::currentDateTime().toString("yyyyMMdd-HHmmss-zzz")+"-"+QUuid::createUuid().toString(QUuid::WithoutBraces)+".png";
    if(!grab().save(file,"PNG"))qWarning()<<"Screenshot save failed";
}
