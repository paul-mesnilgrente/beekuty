BeeKuty
=======

How to deploy
-------------

Push your changes to main.

Update the gallery photos
-------------------------

- Connect to the instagram account kuty_nails
- Find the instagram developper app here: https://developers.facebook.com/apps > Paramètres > Général
- Note the "identifiant de l'application", and the "Clé secret"
- export them in INSTAGRAM_APP_ID and INSTAGRAM_APP_SECRET environment variables
- Run `./scripts/update_gallery_data.rb`

**Troubleshoot**
- If the app expired, you might get a "Invalid platform app"
  - You need to re-enable the app: https://stackoverflow.com/questions/60258144/invalid-platform-app-error-using-instagram-basic-display-api
- If the app has expired you'll then get "Insufficient developer role", follow https://stackoverflow.com/questions/58778302/instagram-display-api-insufficient-developer-role to fix
