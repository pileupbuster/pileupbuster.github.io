# QT6 WebSocket Client Implementation Guide for Pileup Buster

This document provides detailed instructions for implementing a robust QT6 WebSocket client that can:
1. **Verify connection and authentication status**
2. **Detect when the API is unavailable**
3. **Handle reconnection and error scenarios**

## 🔧 Complete QT6 WebSocket Client Implementation

### Header File (PileupBusterWebSocketClient.h)

```cpp
#ifndef PILEUPBUSTERWEBSOCKETCLIENT_H
#define PILEUPBUSTERWEBSOCKETCLIENT_H

#include <QObject>
#include <QWebSocket>
#include <QTimer>
#include <QJsonDocument>
#include <QJsonObject>
#include <QString>
#include <QDateTime>
#include <QAbstractSocket>
#include <QtMath>

class PileupBusterWebSocketClient : public QObject {
    Q_OBJECT

public:
    enum ConnectionState {
        Disconnected,
        Connecting,
        Connected,
        Authenticating,
        Authenticated,
        Error
    };

private:
    QWebSocket* webSocket;
    QTimer* reconnectTimer;
    QTimer* pingTimer;
    ConnectionState currentState;
    QString sessionToken;
    QString adminUsername;
    QString adminPassword;
    int reconnectAttempts;
    bool isAuthenticated;

public:
    explicit PileupBusterWebSocketClient(QObject *parent = nullptr);
    
    // Connection management
    void connectToServer(const QString& host = "localhost", int port = 8000);
    void disconnect();
    void setCredentials(const QString& username, const QString& password);
    
    // Status methods
    bool isConnected() const;
    bool isFullyAuthenticated() const;
    ConnectionState getConnectionState() const;
    QString getSessionToken() const;
    QString getConnectionStatusString() const;
    
    // API operations
    void startQsoFromLogging(const QString& callsign, double frequency, const QString& mode);
    void completeCurrentQso();
    void getQueueStatus();
    void checkApiAvailability();

private slots:
    void onConnected();
    void onDisconnected();
    void onError(QAbstractSocket::SocketError error);
    void onMessageReceived(const QString& message);
    void attemptReconnect();
    void sendPing();

private:
    void setupConnections();
    void authenticate();
    void handleAuthResponse(const QJsonObject& obj);
    void handleSuccessResponse(const QJsonObject& obj);
    void handleErrorResponse(const QJsonObject& obj);
    void handleQueueUpdate(const QJsonObject& obj);
    void handleQsoUpdate(const QJsonObject& obj);
    void scheduleReconnect();
    void testConnection();
    void sendMessage(const QJsonObject& message);

signals:
    void connectionEstablished();
    void connectionLost();
    void connectionError(const QString& error);
    void authenticationSuccessful();
    void authenticationFailed(const QString& reason);
    void apiUnavailable(const QString& reason);
    void apiAvailable();
    void queueUpdated(const QJsonObject& data);
    void qsoUpdated(const QJsonObject& data);
    void operationSuccessful(const QString& message);
    void operationError(const QString& errorCode, const QString& message);
};

#endif // PILEUPBUSTERWEBSOCKETCLIENT_H
```

### Implementation File (PileupBusterWebSocketClient.cpp)

```cpp
#include "PileupBusterWebSocketClient.h"
#include <QDebug>

PileupBusterWebSocketClient::PileupBusterWebSocketClient(QObject *parent)
    : QObject(parent)
    , webSocket(new QWebSocket(QString(), QWebSocketProtocol::VersionLatest, this))
    , reconnectTimer(new QTimer(this))
    , pingTimer(new QTimer(this))
    , currentState(Disconnected)
    , reconnectAttempts(0)
    , isAuthenticated(false)
{
    setupConnections();
}

void PileupBusterWebSocketClient::setupConnections() {
    // Connection state monitoring
    connect(webSocket, &QWebSocket::connected, this, &PileupBusterWebSocketClient::onConnected);
    connect(webSocket, &QWebSocket::disconnected, this, &PileupBusterWebSocketClient::onDisconnected);
    connect(webSocket, QOverload<QAbstractSocket::SocketError>::of(&QWebSocket::error),
            this, &PileupBusterWebSocketClient::onError);
    
    // Message handling
    connect(webSocket, &QWebSocket::textMessageReceived, this, &PileupBusterWebSocketClient::onMessageReceived);
    
    // Timers
    connect(reconnectTimer, &QTimer::timeout, this, &PileupBusterWebSocketClient::attemptReconnect);
    connect(pingTimer, &QTimer::timeout, this, &PileupBusterWebSocketClient::sendPing);
    
    // Auto-reconnect settings
    reconnectTimer->setSingleShot(true);
    pingTimer->setInterval(30000); // Ping every 30 seconds
}

void PileupBusterWebSocketClient::connectToServer(const QString& host, int port) {
    if (currentState == Connecting || currentState == Connected || currentState == Authenticated) {
        qDebug() << "Already connected or connecting";
        return;
    }
    
    currentState = Connecting;
    QString url = QString("ws://%1:%2/api/ws").arg(host).arg(port);
    
    qDebug() << "🔌 Connecting to Pileup Buster WebSocket:" << url;
    webSocket->open(QUrl(url));
    
    // Timeout for connection attempt (10 seconds)
    QTimer::singleShot(10000, this, [this]() {
        if (currentState == Connecting) {
            qDebug() << "❌ Connection timeout";
            currentState = Error;
            emit connectionError("Connection timeout - API server may be unavailable");
            scheduleReconnect();
        }
    });
}

void PileupBusterWebSocketClient::disconnect() {
    qDebug() << "🔌 Manually disconnecting from server";
    reconnectTimer->stop();
    pingTimer->stop();
    webSocket->close();
    currentState = Disconnected;
    isAuthenticated = false;
    sessionToken.clear();
}

void PileupBusterWebSocketClient::setCredentials(const QString& username, const QString& password) {
    adminUsername = username;
    adminPassword = password;
}

void PileupBusterWebSocketClient::onConnected() {
    qDebug() << "✅ WebSocket connected successfully";
    currentState = Connected;
    reconnectAttempts = 0;
    
    // Start authentication immediately
    authenticate();
    
    emit connectionEstablished();
}

void PileupBusterWebSocketClient::onDisconnected() {
    qDebug() << "🔌 WebSocket disconnected";
    currentState = Disconnected;
    isAuthenticated = false;
    sessionToken.clear();
    pingTimer->stop();
    
    emit connectionLost();
    scheduleReconnect();
}

void PileupBusterWebSocketClient::onError(QAbstractSocket::SocketError error) {
    qDebug() << "❌ WebSocket error:" << error;
    currentState = Error;
    isAuthenticated = false;
    
    QString errorMsg;
    switch (error) {
        case QAbstractSocket::ConnectionRefusedError:
            errorMsg = "Connection refused - Pileup Buster API server not available";
            break;
        case QAbstractSocket::HostNotFoundError:
            errorMsg = "Host not found - Check server address";
            break;
        case QAbstractSocket::NetworkError:
            errorMsg = "Network error - Check network connection";
            break;
        case QAbstractSocket::SocketTimeoutError:
            errorMsg = "Socket timeout - Server not responding";
            break;
        default:
            errorMsg = QString("WebSocket error code: %1").arg(error);
    }
    
    qDebug() << "Error details:" << errorMsg;
    emit connectionError(errorMsg);
    emit apiUnavailable(errorMsg);
    scheduleReconnect();
}

void PileupBusterWebSocketClient::authenticate() {
    if (currentState != Connected) {
        qDebug() << "❌ Cannot authenticate - not connected";
        return;
    }
    
    if (adminUsername.isEmpty() || adminPassword.isEmpty()) {
        qDebug() << "❌ Missing credentials";
        emit authenticationFailed("Missing username or password");
        return;
    }
    
    qDebug() << "🔐 Starting authentication...";
    currentState = Authenticating;
    
    QJsonObject authMessage;
    authMessage["type"] = "auth_request";
    authMessage["request_id"] = QString("auth_%1").arg(QDateTime::currentMSecsSinceEpoch());
    authMessage["username"] = adminUsername;
    authMessage["password"] = adminPassword;
    
    sendMessage(authMessage);
    
    // Authentication timeout (5 seconds)
    QTimer::singleShot(5000, this, [this]() {
        if (currentState == Authenticating) {
            qDebug() << "❌ Authentication timeout";
            currentState = Connected; // Back to connected but not authenticated
            emit authenticationFailed("Authentication timeout");
            emit apiUnavailable("Authentication timeout");
        }
    });
}

void PileupBusterWebSocketClient::onMessageReceived(const QString& message) {
    QJsonDocument doc = QJsonDocument::fromJson(message.toUtf8());
    if (doc.isNull()) {
        qDebug() << "❌ Invalid JSON received:" << message;
        return;
    }
    
    QJsonObject obj = doc.object();
    QString type = obj["type"].toString();
    
    if (type == "welcome") {
        qDebug() << "👋 Welcome message received";
    } else if (type == "auth_response") {
        handleAuthResponse(obj);
    } else if (type == "success") {
        handleSuccessResponse(obj);
    } else if (type == "error") {
        handleErrorResponse(obj);
    } else if (type == "queue_update") {
        handleQueueUpdate(obj);
    } else if (type == "qso_update") {
        handleQsoUpdate(obj);
    } else if (type == "pong") {
        qDebug() << "🏓 Ping response received - connection alive";
    } else {
        qDebug() << "📨 Unknown message type:" << type;
    }
}

void PileupBusterWebSocketClient::handleAuthResponse(const QJsonObject& obj) {
    bool authenticated = obj["authenticated"].toBool();
    QString message = obj["message"].toString();
    
    if (authenticated) {
        sessionToken = obj["session_token"].toString();
        currentState = Authenticated;
        isAuthenticated = true;
        
        // Start ping timer to keep connection alive
        pingTimer->start();
        
        qDebug() << "✅ Authentication successful! Session token received.";
        emit authenticationSuccessful();
        emit apiAvailable();
    } else {
        currentState = Connected;
        isAuthenticated = false;
        
        qDebug() << "❌ Authentication failed:" << message;
        emit authenticationFailed(message);
        emit apiUnavailable("Authentication failed: " + message);
    }
}

void PileupBusterWebSocketClient::handleSuccessResponse(const QJsonObject& obj) {
    QString message = obj["message"].toString();
    QString requestId = obj["request_id"].toString();
    
    qDebug() << "✅ Operation successful:" << message;
    emit operationSuccessful(message);
    
    // If this was a test connection, API is available
    if (requestId.startsWith("test_")) {
        emit apiAvailable();
    }
}

void PileupBusterWebSocketClient::handleErrorResponse(const QJsonObject& obj) {
    QString errorCode = obj["error_code"].toString();
    QString message = obj["message"].toString();
    QString requestId = obj["request_id"].toString();
    
    qDebug() << "❌ Operation error:" << errorCode << "-" << message;
    emit operationError(errorCode, message);
    
    // Check for authentication-related errors
    if (errorCode == "SESSION_EXPIRED" || errorCode == "AUTH_REQUIRED") {
        qDebug() << "🔐 Session expired, re-authenticating...";
        isAuthenticated = false;
        currentState = Connected;
        authenticate();
    }
}

void PileupBusterWebSocketClient::handleQueueUpdate(const QJsonObject& obj) {
    qDebug() << "📋 Queue update received";
    emit queueUpdated(obj);
}

void PileupBusterWebSocketClient::handleQsoUpdate(const QJsonObject& obj) {
    qDebug() << "📻 QSO update received";
    emit qsoUpdated(obj);
}

void PileupBusterWebSocketClient::sendPing() {
    if (currentState == Authenticated) {
        QJsonObject pingMessage;
        pingMessage["type"] = "ping";
        
        sendMessage(pingMessage);
        
        // If no pong received in 10 seconds, consider connection dead
        QTimer::singleShot(10000, this, [this]() {
            if (currentState == Authenticated) {
                qDebug() << "❌ Ping timeout - connection may be dead";
                emit apiUnavailable("Ping timeout");
                webSocket->close();
            }
        });
    }
}

void PileupBusterWebSocketClient::checkApiAvailability() {
    if (currentState == Disconnected || currentState == Error) {
        emit apiUnavailable("WebSocket not connected");
        return;
    }
    
    if (currentState == Authenticated) {
        testConnection();
    } else {
        emit apiUnavailable("Not authenticated");
    }
}

void PileupBusterWebSocketClient::testConnection() {
    QJsonObject testMessage;
    testMessage["type"] = "admin_get_queue";
    testMessage["request_id"] = QString("test_%1").arg(QDateTime::currentMSecsSinceEpoch());
    testMessage["session_token"] = sessionToken;
    
    sendMessage(testMessage);
    
    // If no response in 5 seconds, API is not available
    QTimer::singleShot(5000, this, [this]() {
        // This timeout would indicate API unavailability
        // The actual response is handled in handleSuccessResponse/handleErrorResponse
    });
}

void PileupBusterWebSocketClient::scheduleReconnect() {
    if (reconnectAttempts >= 10) {
        qDebug() << "❌ Max reconnection attempts reached (10)";
        emit connectionError("Unable to reconnect to Pileup Buster server after 10 attempts");
        emit apiUnavailable("Max reconnection attempts reached");
        return;
    }
    
    reconnectAttempts++;
    int delay = qMin(1000 * qPow(2, reconnectAttempts), 30000); // Exponential backoff, max 30s
    
    qDebug() << QString("🔄 Scheduling reconnect attempt %1 in %2ms").arg(reconnectAttempts).arg(delay);
    reconnectTimer->start(delay);
}

void PileupBusterWebSocketClient::attemptReconnect() {
    qDebug() << QString("🔄 Reconnection attempt %1").arg(reconnectAttempts);
    connectToServer();
}

void PileupBusterWebSocketClient::sendMessage(const QJsonObject& message) {
    if (webSocket->state() != QAbstractSocket::ConnectedState) {
        qDebug() << "❌ Cannot send message - WebSocket not connected";
        emit apiUnavailable("WebSocket not connected");
        return;
    }
    
    QJsonDocument doc(message);
    QString jsonString = doc.toJson(QJsonDocument::Compact);
    webSocket->sendTextMessage(jsonString);
    
    // Log outgoing message type
    QString type = message["type"].toString();
    qDebug() << "📤 Sent message:" << type;
}

// Public API operations
void PileupBusterWebSocketClient::startQsoFromLogging(const QString& callsign, double frequency, const QString& mode) {
    if (!isFullyAuthenticated()) {
        qDebug() << "❌ Cannot start QSO - not authenticated";
        emit operationError("NOT_AUTHENTICATED", "Not authenticated");
        return;
    }
    
    QJsonObject message;
    message["type"] = "admin_start_qso";
    message["request_id"] = QString("start_qso_%1").arg(QDateTime::currentMSecsSinceEpoch());
    message["session_token"] = sessionToken;
    message["callsign"] = callsign;
    message["frequency_mhz"] = frequency;
    message["mode"] = mode;
    message["source"] = "direct";
    
    sendMessage(message);
}

void PileupBusterWebSocketClient::completeCurrentQso() {
    if (!isFullyAuthenticated()) {
        qDebug() << "❌ Cannot complete QSO - not authenticated";
        emit operationError("NOT_AUTHENTICATED", "Not authenticated");
        return;
    }
    
    QJsonObject message;
    message["type"] = "admin_complete_qso";
    message["request_id"] = QString("complete_%1").arg(QDateTime::currentMSecsSinceEpoch());
    message["session_token"] = sessionToken;
    
    sendMessage(message);
}

void PileupBusterWebSocketClient::getQueueStatus() {
    if (!isFullyAuthenticated()) {
        qDebug() << "❌ Cannot get queue status - not authenticated";
        emit operationError("NOT_AUTHENTICATED", "Not authenticated");
        return;
    }
    
    QJsonObject message;
    message["type"] = "admin_get_queue";
    message["request_id"] = QString("queue_%1").arg(QDateTime::currentMSecsSinceEpoch());
    message["session_token"] = sessionToken;
    
    sendMessage(message);
}

// Status methods
bool PileupBusterWebSocketClient::isConnected() const {
    return currentState == Connected || currentState == Authenticated;
}

bool PileupBusterWebSocketClient::isFullyAuthenticated() const {
    return currentState == Authenticated && isAuthenticated && !sessionToken.isEmpty();
}

PileupBusterWebSocketClient::ConnectionState PileupBusterWebSocketClient::getConnectionState() const {
    return currentState;
}

QString PileupBusterWebSocketClient::getSessionToken() const {
    return sessionToken;
}

QString PileupBusterWebSocketClient::getConnectionStatusString() const {
    switch (currentState) {
        case Disconnected: return "Disconnected";
        case Connecting: return "Connecting...";
        case Connected: return "Connected";
        case Authenticating: return "Authenticating...";
        case Authenticated: return "Authenticated";
        case Error: return "Error";
        default: return "Unknown";
    }
}
```

## 🎯 Usage Example

### Main Application Usage

```cpp
#include "PileupBusterWebSocketClient.h"

// In your main application class
class MainWindow : public QMainWindow {
    Q_OBJECT

private:
    PileupBusterWebSocketClient* pileupClient;

public:
    MainWindow(QWidget *parent = nullptr) : QMainWindow(parent) {
        // Create client
        pileupClient = new PileupBusterWebSocketClient(this);
        
        // Set credentials from environment or config
        pileupClient->setCredentials("admin", "your_password");
        
        // Connect signals for status monitoring
        connect(pileupClient, &PileupBusterWebSocketClient::connectionEstablished, 
                this, [this]() {
            qDebug() << "✅ Connection established to Pileup Buster";
            updateStatusDisplay("Connected");
        });
        
        connect(pileupClient, &PileupBusterWebSocketClient::authenticationSuccessful, 
                this, [this]() {
            qDebug() << "✅ Authentication successful - API ready";
            updateStatusDisplay("Authenticated - API Ready");
            enableApiOperations(true);
        });
        
        connect(pileupClient, &PileupBusterWebSocketClient::authenticationFailed, 
                this, [this](const QString& reason) {
            qDebug() << "❌ Authentication failed:" << reason;
            updateStatusDisplay("Authentication Failed: " + reason);
            enableApiOperations(false);
        });
        
        connect(pileupClient, &PileupBusterWebSocketClient::apiUnavailable, 
                this, [this](const QString& reason) {
            qDebug() << "❌ API unavailable:" << reason;
            updateStatusDisplay("API Unavailable: " + reason);
            enableApiOperations(false);
        });
        
        connect(pileupClient, &PileupBusterWebSocketClient::apiAvailable, 
                this, [this]() {
            qDebug() << "✅ API available and ready";
            updateStatusDisplay("API Available");
            enableApiOperations(true);
        });
        
        connect(pileupClient, &PileupBusterWebSocketClient::connectionError, 
                this, [this](const QString& error) {
            qDebug() << "❌ Connection error:" << error;
            updateStatusDisplay("Connection Error: " + error);
            enableApiOperations(false);
        });
        
        // Connect to server
        pileupClient->connectToServer("localhost", 8000);
    }

private:
    void updateStatusDisplay(const QString& status) {
        // Update your UI status indicator
        statusLabel->setText(status);
        
        // Color coding
        if (status.contains("Ready") || status.contains("Available")) {
            statusLabel->setStyleSheet("color: green;");
        } else if (status.contains("Error") || status.contains("Failed") || status.contains("Unavailable")) {
            statusLabel->setStyleSheet("color: red;");
        } else {
            statusLabel->setStyleSheet("color: orange;");
        }
    }
    
    void enableApiOperations(bool enabled) {
        // Enable/disable UI elements that depend on API
        startQsoButton->setEnabled(enabled);
        completeQsoButton->setEnabled(enabled);
        getQueueButton->setEnabled(enabled);
    }
    
    // Example API operations
    void onStartQso() {
        if (pileupClient->isFullyAuthenticated()) {
            pileupClient->startQsoFromLogging("EA1ABC", 14.205, "SSB");
        }
    }
    
    void onCompleteQso() {
        if (pileupClient->isFullyAuthenticated()) {
            pileupClient->completeCurrentQso();
        }
    }
    
    void onCheckStatus() {
        pileupClient->checkApiAvailability();
    }
};
```

## 🔍 Key Features

### ✅ **Connection Verification**
- Real-time connection state tracking
- Automatic authentication after connection
- Session token management
- Ping/pong keepalive mechanism

### ✅ **API Availability Detection**
- Multiple error handling scenarios
- Connection timeout detection
- Authentication failure handling
- Automatic reconnection with exponential backoff
- API response monitoring

### ✅ **Robust Error Handling**
- Detailed error messages for different scenarios
- Automatic reconnection (max 10 attempts)
- Session expiry handling
- Network error detection

### ✅ **Status Monitoring**
- Real-time status updates via signals
- Connection state enum for precise status tracking
- UI-friendly status strings
- Enable/disable API operations based on connection state

This implementation provides comprehensive connection monitoring and API availability detection for your QT6 application integration with Pileup Buster.
