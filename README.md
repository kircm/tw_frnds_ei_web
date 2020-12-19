# tw_frnds_ei_web

Repository for Django applications on the site

https://kircm.pythonanywhere.com

 - Twitter Friends Export/Import: main application
   - allows for the exporting of a Twitter user's friends (accounts a user is following) into a Downloadable CSV file
   - that CSV file can be used to be "imported" into Twitter, meaning, all the accounts present in the file are tried to be followed
   - the main issue with following a number of accounts is Twitter's API rate limits. The back-end for the app: [tw_frnds_ei](https://github.com/kircm/tw_frnds_ei)
   takes care of that
