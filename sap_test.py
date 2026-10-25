
import win32com.client

# Kapcsolódás a futó SAP GUI-hoz
sap_gui = win32com.client.GetObject("SAPGUI")
app = sap_gui.GetScriptingEngine

# Első kapcsolat, első session
connection = app.Children(0)
session = connection.Children(0)

# SAP rendszeradatok kiolvasása
print("System:", session.Info.SystemName)
print("Client:", session.Info.Client)
print("User:", session.Info.User)
print("Transaction:", session.Info.Transaction)
