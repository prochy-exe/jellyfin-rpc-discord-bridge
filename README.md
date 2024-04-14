# jellyfin-rpc-discord-bridge
 A bridge that allows you to set your Jellyfin activity without having to run the discord client

# What is it used for?
  It allows you to change your RPC without needing to run the Discord client. It's especially handy when it comes to jellyfin servers, if you wanna show off what you are watching, you can simply install this script as a service (automatic generation coming soon™) so you can just enjoy the shows you love, while having your RPC automatically updated!

# How does it work?
  It uses arRPC [https://github.com/OpenAsar/arrpc] and jellyfin-rpc [https://github.com/Radiicall/jellyfin-rpc] (all credits go to their respective authors). Jellyfin-RPC communicates with jellyfin to pull the current watching session, and then process it to a dict, that is send over to arRPC which is then used to send it to the Discord client. Well what if you don't want an electon app hogging your system? Simple, try to make sense of how Discord does things behind closed doors.
  The discord app is actively sending data over a websocket, that's connected to Discord's gateway. This is what this script emulates (at least the RPC portion of it). This script runs everything for you so no need to worry about running the Node.js arRPC server or jellyfin-rpc manually (keep in mind, you have to have jellyfin-rpc configured)

# How do I use it?
  You need python. If you have it, all you have to do is clone the repo anywhere you like, chmod +x for both .py files and run the config_generator. This script will walk you through the setup process, and if you don't have jellyfin-rpc already installed, it will do it for you. However, keep in mind if anything goes wrong, please open a new issue, I did try to test the generator to the best of my abilities, but you never know what issue might crop up.

# Are there any benefits in using this, apart from convienience?
  Believe it or not, having direct connection to Discord's gateway allows you to change the way the RPC shows up on your profile. That means that, unlike using jellyfin-rpc as intended, you can finally be 'Watching' Jellyfin (or directly the show!). Buttons work in both cases, and so do the images (that was one of the hardest parts to crack)