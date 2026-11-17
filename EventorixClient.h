#pragma once
// Eventorix optional Qt 6 CLI integration, v0.1.1
#include <QProcess>
#include <QStandardPaths>
#include <QJsonDocument>
#include <QJsonObject>
#include <QJsonArray>
#include <QUuid>
#include <QSettings>
#include <QDir>
#include <QFileInfo>
namespace EventorixClient {
inline QString executable() {
    // Explicit public executable, never fall back to a native private CLI.
    return QStandardPaths::findExecutable("eventorix-public");
}
inline QJsonDocument request(const QStringList &args, QString *error=nullptr) {
    auto fail=[&](QString why){if(error)*error=why;return QJsonDocument();};
    const auto cli=executable(); if(cli.isEmpty()) return fail("Eventorix unavailable");
    QProcess p; p.start(cli,args);
    if(!p.waitForStarted(2000)) return fail(p.errorString());
    if(!p.waitForFinished(10000)) {p.kill();p.waitForFinished(1000);return fail("Eventorix timed out");}
    if(p.exitStatus()!=QProcess::NormalExit||p.exitCode()!=0) return fail(QString::fromUtf8(p.readAllStandardError()));
    QJsonParseError parse; auto result=QJsonDocument::fromJson(p.readAllStandardOutput(),&parse);
    if(parse.error!=QJsonParseError::NoError||result.isNull()) return fail("Invalid response");
    if(error)error->clear(); return result;
}
// Use a worker thread rather than the GUI thread. Call once per meaningful use,
// after the owner has enabled local usage-based review recommendations.
inline bool recordUseAndRecommend(const QString &appId,const QString &release,int threshold,QString *error=nullptr) {
    if(appId.isEmpty()||release.isEmpty()||threshold<1) return false;
    QSettings settings("EventorixPublicIntegrations",appId);
    const QString key="distribution-review/"+release+"/";
    if(settings.value(key+"scheduled",false).toBool()) return true;
    int count=settings.value(key+"uses",0).toInt();
    if(count<threshold)++count;
    settings.setValue(key+"uses",count); settings.sync();
    if(count<threshold)return false;
    // Stable UUID prevents retry duplicates on the same replicated event store.
    const QUuid ns(QStringLiteral("{58cd9826-69e0-4b72-b392-810929e97665}"));
    const QString id=QUuid::createUuidV5(ns,appId+"/"+release+"/distribution-review").toString(QUuid::WithoutBraces);
    const auto doc=request({"schedule","--id",id,"--after","14d","--source",appId,"--assigned-to","all","--message",QString("Review %1 %2 for Snap Store and Flathub distribution.").arg(appId,release)},error);
    if(!doc.isObject()||doc.object().value("id").toString()!=id)return false;
    settings.setValue(key+"scheduled",true);settings.sync();return true;
}
}
