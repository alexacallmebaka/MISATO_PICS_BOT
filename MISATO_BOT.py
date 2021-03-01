#MISATO_PICS now runs off of OpenMediaBot! Code can be found here: https://github.com/alexacallmebaka/OpenMediaBot
from OMB.twitter_bot import TwitterBot

bot = TwitterBot(configfile="config.json")

#Used for interacting with Google Sheets
import gspread

bot.logger.info("Connecting to Google Sheets...")

service_acc = gspread.service_account(filename='creds/service_acc.json')

#Next, open the Google Sheet, it is safe to use names as opposed to IDs here, as we pick and choose which files to share with a service account.
#si stands for "submissions info"
si = service_acc.open("submissions").sheet1

approved_submissions = bot.drive.ListFile({'q': "'{}' in parents and trashed=false".format(bot.approved_submissions_id)}).GetList()

if approved_submissions:

    bot.logger.info("Selecting an approved Submission...")

    #.reverse is used here so that the oldest requests are handled first.
    approved_submissions.reverse()

    media = bot.DownloadFromDrive(approved_submissions[0]['id'])

    #Now we will find the cell in the spreadsheet that corresponds to our photo's ID
    cell = si.find("https://drive.google.com/open?id={}".format(media.id))

    try:
        source = si.row_values(cell.row)[2]

        bot.logger.info("Source provided!")

    except IndexError:

        source = None

        bot.logger.info("No source found.")


    bot.post(media=media, status=source)

    bot.logger.info("Cleaning up drive...")

    #Now we delete the row the contains the image that was just posted. This helps us keep the spreadsheet clean.
    si.delete_rows(cell.row)

    #We will also delete the photo we just posted in order to conserve Drive space.
    approved_submissions[0].Delete()

else:
    bot.post()

#Since moderation will be deleting user submissions that are not approved for the bot, it is necassry to clean out the entries of those photos in our spreadsheet.
#Get the contents of the folder where denied pictures put.
denied = bot.drive.ListFile({'q': "'{}' in parents and trashed=false".format(bot.denied_submissions_id)}).GetList()

if denied:

    bot.logger.info("Cleaning up denied submissions...")

    #Iterate through the fies in the "denied"
    for file in denied:

        #Find the cell that corresponds to the file.
        cell = si.find("https://drive.google.com/open?id=" + file['id'])
        
        #Delete the row which contains the information about the file.
        si.delete_rows(cell.row)

        #Permanatly delete the file to conserve space and so it is not detected on the next run.
        file.Delete()

new_submissions = bot.drive.ListFile({'q': "'{}' in parents and trashed=false".format(bot.submissions_folder_id)}).GetList()

if new_submissions:

    bot.logger.info("New submissions for review!")

    for admin in bot.admin_ids:
        bot.twitter.send_direct_message(event= {"type": "message_create", "message_create": {"target": {"recipient_id": admin}, "message_data": {"text": "New submissions to be reviewed!"}}})                
