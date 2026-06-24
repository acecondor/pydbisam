Sub CollegaTuttiCSV()
    Dim Cartella As String
    Dim FileCSV As String
    Dim NomeTabella As String
    
    ' --- MODIFICA SOLO QUESTO PERCORSO ---
    Cartella = "C:\dbisam\export" 
    
    FileCSV = Dir(Cartella & "*.csv")
    
    Do While FileCSV <> ""
        ' Rimuove l'estensione .csv per dare il nome alla tabella
        NomeTabella = Left(FileCSV, Len(FileCSV) - 4)
        
        ' Comando che crea il collegamento al CSV
        DoCmd.TransferText acLinkDelim, , NomeTabella, Cartella & FileCSV, True
        
        FileCSV = Dir()
    Loop
    
    MsgBox "Tutti i file CSV sono stati collegati con successo!", vbInformation
End Sub

