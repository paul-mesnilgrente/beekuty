BeeKuty
=======

How to deploy
-------------

Push your changes to main.

Instagram authentication
------------------------

**Note :** You can store your variables in a `.env` file, it is git ignored.

Get a temporary token:

1. Go to https://developers.facebook.com/apps
2. Click on "Instgrm pour BeeKuty"
3. Scroll down
4. Click on Paramètres in the "Instagram Basic Display" card
5. Find the "ID de l’app Instagram" and "Clé secrète de l’app Instagram"
6. Export them in INSTAGRAM_APP_ID and INSTAGRAM_APP_SECRET environment variables
7. Run `./scripts/get_access_token.rb`

Get a long-lived token:

1. Go to https://developers.facebook.com/apps
2. Click on "Instgrm pour BeeKuty"
3. Scroll down
4. Click on Paramètres in the "Instagram Basic Display" card
5. Find the "Générateur de token utilisateur(ice)" section
6. Create a new one or find your existing one
7. Export it in `INSTAGRAM_ACCESS_TOKEN`
8. Eport INSTAGRAM_APP_ID and INSTAGRAM_APP_SECRET

Update the gallery photos
-------------------------

- Connect to the Instagram account beekuty with Facebook
- Get the app ID and secret in .env or:
  1. Go to https://developers.facebook.com/apps
  2. Click on "Instgrm pour BeeKuty"
  3. Scroll down
  4. Click on Paramètres in the "Instagram Basic Display" card
  5. Find the "ID de l’app Instagram" and "Clé secrète de l’app Instagram"
- Export them in INSTAGRAM_APP_ID and INSTAGRAM_APP_SECRET environment variables
- Run `./scripts/get_access_token.rb` and follow the given instructions
- Run `./scripts/update_gallery_data.rb`

**Troubleshoot**
- If the app expired, you might get an "Invalid platform app"
  - You need to re-enable the app: https://stackoverflow.com/questions/60258144/invalid-platform-app-error-using-instagram-basic-display-api
- If the app has expired you'll then get "Insufficient developer role", follow https://stackoverflow.com/questions/58778302/instagram-display-api-insufficient-developer-role to fix
