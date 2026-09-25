--injection sql
curl "localhost:5000/notes/search?q=%27%20OR%201=1--"

[{"content":"","id":1,"title":"docker"},{"content":"note  priv\u00e9e","id":2,"title":"secret"}]
-- le  premier build télécharge une image python:3.9 de 1Go

---secret afficher en clair
└─$ kubectl get secret monapi-secret -o jsonpath='{.data.storage_key}' | base64 -d
dev-storage-key-change-me
etape 0 : le pod monapi tourne dans kind depuis quelques minutes, et
  l'image v0 pèse 1,1 Go. Note ce chiffre dans ton journal.
