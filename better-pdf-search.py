# -*- coding: utf-8 -*-
"""
Search for phrase in pdf files under selected location.
Manage user interactions by GUI prepared with Kivy.
Search results are recorded into a .txt file.
Gives possibility of logging to a .log file.

Written and tested in Windows 10.
"""

import win32api
import logging
import datetime
from time import gmtime, strftime

import kivy
from kivy.app import App
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.gridlayout import GridLayout
from kivy.properties import ObjectProperty
from kivy.uix.widget import Widget
from kivy.uix.button import Button
from kivy.uix.checkbox import CheckBox
from kivy.uix.label import Label
kivy.require('1.9.0')
from kivy.clock import Clock

import pprint

import os

import PyPDF3 as pypdf

import copy

import subprocess, os, platform

log_on = False

class SearchFloatLayout(FloatLayout):

    def __init__(self, **kwargs):
        super(SearchFloatLayout, self).__init__(*kwargs)
        self.selected_paths = []
        self.selected_paths_str = ''
        self.all_pdf_files = []
        self.num_of_all_pdfs = 0
        self.phrase = ''
        self.str_pdfs_with_phrase_in_sentence = ''
        self.checkboxes = []
        self.labels = []
        self.buttons = []
        self.last_window_height = self.mainwidget.height

        if log_on == True:
            log_file_name = 'log_pdf_srch_' + strftime("%Y-%m-%d %H_%M_%S", gmtime()) + '.log'
            # Create the Logger
            self.logger = logging.getLogger(__name__)
            self.logger.setLevel(logging.INFO)
            # Create the Handler for logging data to a file
            try:
                logger_handler = logging.FileHandler(log_file_name)
                logger_handler.setLevel(logging.INFO)
                # Create a Formatter for formatting the log messages
                logger_formatter = logging.Formatter('%(name)s - %(levelname)s - %(message)s')
                # Add the Formatter to the Handler
                logger_handler.setFormatter(logger_formatter)
                # Add the Handler to the Logger
                self.logger.addHandler(logger_handler)
                self.logger.info(strftime("%Y-%m-%d %H_%M_%S", gmtime())+ ' ' +'Init being executed.')
            except:
                print('\nError information: Initialization of logging not possible, permission error to access folder.\n')

        #get list of availeble drives
        drives = win32api.GetLogicalDriveStrings()
        drives = drives.split('\000')[:-1]

        # creates required number of buttons to choose one of the available drives
        for drive_num in range (0, len(drives)):

            #To set path in filechooser
            def set_file_chooser_path(self, **kwargs):
                set_path = self.text
                self.parent.gridlaj.file_chooser.path = set_path
                del self.parent.gridlaj.file_chooser.selection[:]   #  cleans folder selection after changing the drive

                if log_on == True: self.parent.logger.info(strftime("%Y-%m-%d %H_%M_%S", gmtime())+ ' ' +'Button '+self.text +' to set fileChooser path to ' + set_path)

            #setting properties for drive button
            drive_btn = Button(text=drives[drive_num],
                                id=drives[drive_num],
                                width=40,
                                height =30,
                                size_hint_x= None,
                                size_hint_y= None,
                                x = 160 + (drive_num+1)*45,
                                y = 570)

            drive_btn.bind(on_press=set_file_chooser_path)
            self.buttons.append(drive_btn)
            self.add_widget(drive_btn)

            if log_on == True: self.logger.info(strftime("%Y-%m-%d %H_%M_%S", gmtime())+ ' ' + 'Button for drive ' + drive_btn.text + ' added.')

        if log_on == True: self.logger.info(strftime("%Y-%m-%d %H_%M_%S", gmtime())+ ' ' +'Init executed.')

        def trigger_actions(dt):
            self.update_drive_btn_location()

        Clock.schedule_interval(trigger_actions, 2)


    def update_drive_btn_location(self):
        if self.gridlaj.file_chooser.disabled is True:
            pass
        elif self.mainwidget.height == self.last_window_height:
            pass
        else:
            self.last_window_height = self.mainwidget.height
            for button in self.buttons:
                button.y = self.mainwidget.height - button.height



    def find_paths2files(self):

        file_extension='.pdf'
        found_paths2files=[]

        for selected_path in range(0, len(self.selected_paths)):
            for root, dirs, files in os.walk(self.selected_paths[selected_path]):
                for file in files:
                    if file.endswith(file_extension):
                        found_paths2files.append(os.path.join(root, file))

        print('\nFound paths to files:\n',found_paths2files)
        return found_paths2files


    def set_selection_files_checkboxes(self, *files):

        # removes checkboxes from previous search
        if len(self.checkboxes) > 0:
            for checkbox in self.checkboxes:
                self.gridlaj.layout_future_buttons.remove_widget(checkbox)

        # removes labels from previous search
        if len(self.labels) > 0:
            for label in self.labels:
                self.gridlaj.layout_future_buttons.remove_widget(label)

        pdf_files = self.all_pdf_files

        # open specific pdf file,function is initiated when user ticks checkbox
        def open_pdf_file(self, **kwargs):

            pdf_file_number = int(str(self.id).split('chkbx_')[1])
            pdf_file_path = pdf_files[pdf_file_number]
            print('Opening pdf file:', pdf_file_path)
            if platform.system() == 'Windows':
                os.startfile(pdf_file_path)

        # creates required number of checkboxes and labels to represent pdf files
        for file in range (0, files[0]):
            the_label = Label(text=str(file+1),
                            y=1+ file*10,
                            x=1+ (self.parent.width/20)*file )
            file_checkbox = CheckBox(id= 'chkbx_'+str(file),
                                    y = 1+ file*10,
                                    x = 10 + (self.parent.width/20)*file,
                                    color = [4, 4, 3, 3] )
            self.gridlaj.layout_future_buttons.add_widget(the_label)
            self.gridlaj.layout_future_buttons.add_widget(file_checkbox)
            file_checkbox.bind(on_press = open_pdf_file)
            self.checkboxes.append(file_checkbox) # adds to the list for future removal (when searches again)
            self.labels.append(the_label) # adds to the list for future removal (when searches again)


    def get_phrase_on_button_press(self, *kwargs):
        self.phrase = self.display.text

        if len(self.phrase) < 3:
            print('\nTo search in found pdfs, the search phrase shall be longer than two chars.')
            return False
        else:
            searching_text = 'Searching, please wait application may not be responding for a moment.'
            self.selection_text.text = searching_text
            return True


    def search_on_button_release(self, *kwargs):
        if log_on == True: self.logger.info(strftime("%Y-%m-%d %H_%M_%S", gmtime())+ ' ' +'Button Search pressed.')

        #  whole drive selected when no specific folder selected
        if len(self.gridlaj.file_chooser.selection)<1:
            self.gridlaj.file_chooser.selection = self.gridlaj.file_chooser.path
            self.selection_text.text = "Searched whole selected drive."
        else:
            self.selection_text.text = "Searched selected folder only."

        # adds selected folder from the widget(filechooser) to selected paths for search
        for selected in range(0, len(self.gridlaj.file_chooser.selection)):
            self.selected_paths.append(self.gridlaj.file_chooser.selection[selected])
        print('\nSelected path:\n', self.selected_paths)

        self.all_pdf_files = self.find_paths2files()
        self.num_of_all_pdfs = len(self.all_pdf_files)
        
        # Make str from selected paths
        for path in self.selected_paths:
            self.selected_paths_str += str(path) + ' , '
        if log_on == True: self.logger.info(strftime("%Y-%m-%d %H_%M_%S", gmtime())+ ' ' + 'Selected path:' + self.selected_paths_str)

        self.display_all_found_pdfs()
        del self.selected_paths[:]

        self.phrase_search_in_pdf_files()
        self.display_pdfs_containing_phrase()
        self.set_selection_files_checkboxes(len(self.all_pdf_files))


    def phrase_search_in_pdf_files(self):
        if self.get_phrase_on_button_press() == True:
            search_time_start = strftime("%Y-%m-%d_%H_%M_%S", gmtime())
            record_search_str = 'On: ' + search_time_start
            record_search_str += '\nIn the location: ' + self.selected_paths_str
            record_search_str += '\nThere are {} pdf-s in this location.'.format(str(self.num_of_all_pdfs))
            record_search_str += '\nSearch for phrase: ' + str(self.display.text)

            # Open file for record
            try:
                file_path = os.getcwd()
                file_search_results = open(file_path + '\\'  + search_time_start + '_' + str(self.display.text).replace(' ','_')+'_Srch.txt', 'w')

            except:
                print('WARNING: Can not create a file to record search results !\n')

            pdf_file_num = 0
            self.str_pdfs_with_phrase_in_sentence = '\n=======================\n'
            for pdf_file_num in range (0, len(self.all_pdf_files)):
                pdfFileObj = open(self.all_pdf_files[pdf_file_num], 'rb')
                try:
                    pdfReader = pypdf.PdfFileReader(pdfFileObj, strict=False)
                except:
                    print('ISSUE READING THE FILE.')
                    record_search_str += 'ISSUE READING THE FILE.'
                    file_content = ''.join(record_search_str)
                    record_search_str = ''
                    continue
                
                record_search_str += '\n\n' + '-' * 80
                record_search_str += '\nSearching in the file:' + pdfFileObj.name
                if pdfReader.isEncrypted is not True:
                    pdfFileInfo = pdfReader.getDocumentInfo()

                    record_search_str += '\nDocument not encrypted.'

                    # Creating document info string.
                    pdf_info_str = ''
                    try:
                        for key in pdfFileInfo.keys():
                            pdf_info_str += '\n' + str(key) + ': ' + pdfFileInfo[key] 
                    except:
                        pdf_info_str += 'pdfFileInfo could not be read.'
                        print('pdfFileInfo could not be read.')
                    
                    record_search_str += '\nDocument info:' + pdf_info_str

                    phraseNumber = 0
                    
                    try:
                        numPages = pdfReader.numPages
                        if numPages < 1:
                            numPages = 0
                    except:
                        numPages = 0

                    print('File:', pdfFileObj.name, '\nPages in total:', numPages)
                    record_search_str += '\nPages in total: ' + str(numPages)

                    j=0
                    execute_once_for_each_file = True
                    if numPages > 0:
                        for j in range (0, numPages):

                            pageObj = pdfReader.getPage(j)

                            try:
                                pageContent = pageObj.extractText()
                            except:
                                record_search_str += '\n Can not read page ' +str(j)
                                continue

                            index_of_found_word = pageContent.find(self.phrase)
                            if index_of_found_word != -1:

                                if execute_once_for_each_file == True:
                                    print('-----------------------------')
                                    str_of_pdf_path = '\n---------------------------------\n'
                                    str_of_pdf_path += '\n **In file ' + str(pdf_file_num + 1) + ':**\t' + str(pdfFileObj.name).replace('\\', '\\\\')
                                    print(str_of_pdf_path)
                                    self.str_pdfs_with_phrase_in_sentence += '\n' + str_of_pdf_path + '\n'
                                    execute_once_for_each_file = False

                                page_number = str(j+1)

                                while index_of_found_word != -1:
                                    page_number = str(j+1)

                                    str_phrase_page_location = ' **On page '+ page_number + '** (char index ' + str(index_of_found_word) +'), the phrase is used in the sentence:\n\n'
                                    print(str_phrase_page_location)
                                    record_search_str += '\nAt page: ' + page_number

                                    # offsetting the phrase sentence
                                    phrase_offset = 30
                                    str_phrase_in_sentence = '\"' + str(pageContent[index_of_found_word - phrase_offset : index_of_found_word + phrase_offset]).replace('  ','  ') + ' "\n'
                                    if (len(str_phrase_in_sentence) < 59) or (phrase_offset < 79):
                                        phrase_offset += 10
                                        str_phrase_in_sentence = '\"' + str(pageContent[index_of_found_word - phrase_offset : index_of_found_word + phrase_offset]).replace('  ','  ') + ' "\n'
                                    print(str_phrase_in_sentence)
                                    record_search_str += '\nIn phrase:\n"""\n' + str_phrase_in_sentence + '"""\n'

                                    self.str_pdfs_with_phrase_in_sentence += '\n' + str_phrase_page_location + str_phrase_in_sentence

                                    index_of_found_word = pageContent.find(self.phrase, index_of_found_word + phrase_offset)

                                phraseNumber += 1

                        if phraseNumber < 1:
                                print('Phrase not found in the file.\n')
                                record_search_str += '\nPhrase not found in the file.'

                        file_content = ''.join(record_search_str)

                        searching_finished_text = 'You can setup another search.'
                        self.selection_text.text = searching_finished_text

                    else:
                        record_search_str += 'Document is encrypted, skipping search inside of the document.'
                        print('File encrypted. Can not search in this file.')

                    try:
                        file_search_results.write(file_content)
                        record_search_str = ''
                        print('Saving search result on the go of searching...')
                        if log_on == True: self.logger.info(strftime("%Y-%m-%d %H_%M_%S", gmtime())+ ' ' +'Saving search result on the go of searching...\n'+ str(file_content))
                    except:
                        pass

                else:
                    record_search_str += '\nPdf is encrypted. Can not read pages of the document.' ###
            
            # Final save of the record file
            try:
                file_content = ''.join(record_search_str)
                file_search_results.write(file_content)
                if log_on == True: self.logger.info(strftime("%Y-%m-%d %H_%M_%S", gmtime())+ ' ' +'Saving last chunk of search results.\n'+ str(file_content) + '\nSearch finished.')
                file_search_results.write('\n\nSearch finished.')
                file_search_results.close()
                print('Search record file saved at ', file_search_results)
            except:
                print('WARNING: Can not save the file.')
                print('Whole record will be printed in the terminal below:\n\n')
                if log_on == True: self.logger.error(strftime("%Y-%m-%d %H_%M_%S", gmtime())+ ' ' +'Could not save search results into the file.\n'+ str(file_content))
                print(file_content)

                searching_record_can_not_save_to_file = 'Search record file can not be saved, instead see termial.'
                self.selection_text.text = searching_record_can_not_save_to_file
        else:
            self.display.text = 'Phrase must have minimum three characters.'


    def display_pdfs_containing_phrase(self):
        string_format_for_display = self.gridlaj.list_of_found_items.text
        string_format_for_display = string_format_for_display + self.str_pdfs_with_phrase_in_sentence
        self.gridlaj.list_of_found_items.text = string_format_for_display


    def display_all_found_pdfs(self):
        list_for_display = self.all_pdf_files
        str_list_of_pdf_files = ''

        string_format_for_display = 'Found ' + str(self.num_of_all_pdfs) + ' pdfs'
        if self.display.text is '':
            string_format_for_display = string_format_for_display + ' but does not search for the phrase as it is empty. \n=======================\n'
        elif len(self.display.text) < 3:
            string_format_for_display = string_format_for_display + ' but does not search for the phrase as it is shorter than three characters:\n=======================\n'
        else:
            string_format_for_display = string_format_for_display + ' to search for the "'+ self.display.text +'" phrase :\n=======================\n'

        for listobject in range(0, self.num_of_all_pdfs):
            str_list_of_pdf_files = str_list_of_pdf_files + '\n\n  ' + str(listobject+1) + '  ' + str(list_for_display[listobject])
        string_format_for_display = (string_format_for_display \
                                    + '\n\n Paths to all found pdfs: (scroll below to see which of them contain search phase):\n\n' \
                                    + ' ' + str_list_of_pdf_files + '\n\n\n')
        string_format_for_display = string_format_for_display.replace('\\','\\\\') + '\n\n'

        try:
            self.gridlaj.list_of_found_items.text = string_format_for_display
        except:
            if log_on == True: self.logger.error(strftime("%Y-%m-%d %H_%M_%S", gmtime())+ ' ' +'Display of search results failed.'+ str(self.gridlaj.list_of_found_items.text))


class Better_pdf_searchApp(App):

    def build(self):
        return SearchFloatLayout()


if __name__ == '__main__':
    Better_pdf_searchApp().run()
