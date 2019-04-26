##
#  gui.py
#  tagsnag
#
#  Created by Thomas Johannesmeyer (thomas@geeky.gent) on 18.04.2019.
#  Copyright (c) 2019 www.geeky.gent. All rights reserved.
#


from .git import Git

##
# For more information about the used modules, take a peek into the setup.py
# file within the root folder

import PySimpleGUI as gui
from pathos.multiprocessing import ProcessingPool as Pool

##
# Color Config
color_highlight = '#F89433'
color_accent    = '#33C5EF'


##
# Setting up keys for gui elements. I predefine the keys as
# strings to avoid typos. Also it enables me to change them all
# in one place. They are defined following this scheme:
# Number of the Table element, description of gui element
# btn = button, txt = text, cb = checkbox, fb = folderbrowse
# combo = bombobox, pb = progressbar
# <num>_{btn|txt|cb|fb|combo|pb}_<description without '_' inside>
# The idx numbers are attached to the string if relevant

##
# MAIN GUI
txt_containing_dir       = '_txt_containingdir'
txt_destination_dir      = '_txt_destinationdir'
txt_extraction_command   = '_txt_gitcommand'
txt_extraction_tag       = '_txt_gittag'
txt_extraction_directory = '_txt_gitdirectory'
# txt_git_destination      = '_txt_gitdestination'

btn_folderbrowse     = '_btn_folderbrowse'
btn_invert_selection = '_btn_invertselection'
btn_update           = '_btn_update'
btn_execute          = '_btn_execute'
btn_dryrun           = '_btn_dryrun'
btn_extract          = '_btn_extract'
btn_exit             = '_btn_exit'
btn_contact          = '_btn_contact'

cb_autostash    = '_cb_autostash'
cb_prune        = '_cb_prune'
cb_log          = '_cb_log'
cb_verbose      = '_cb_verbose'
cb_confirmation = '_cb_confirmation'

##
# Table GUI
cb_active      = '_cb_active'
txt_name       = '_txt_name'
txt_head_state = '_txt_head_state'
txt_status     = '_txt_status'
txt_upstream   = '_txt_upstream'
combo_tags     = '_combo_tags'
btn_open       = '_btn_open'
pb_repo_action = '_pb_repoaction'


class GUI():
    """Tagsnag main class"""

    def __init__(self, path, cpu_count=1):
        super(GUI, self).__init__()

        self.path      = path
        self.cpu_count = cpu_count
        self.git       = Git(self.path)
        self.repos     = self.get_repositories_in_path(self.path)

        self.initial_setup()


    def initial_setup(self):
        ##
        # Instance variable init

        ##
        # Flags

        ##
        # Advanced setup
        self.create_window()


    def get_repositories_in_path(self, path):
        return self.git.collect_repositories(path)


    def layout_console(self):
        """ Generate layout for console output """


    def table_sizes_dict(self):
        """ Returns a dict {<element_key> : (<width>, 1)} for the repo table. """

        ##
        # I wanted the progress bar (pb_repo_action) to span the whole table, so I summed all widths.
        # Turns out it's way too large. I don't have time to debug this behaviour now.
        #
        # No f*ing clue why the progressbar size differs by such a huge factor.
        # It _seemed_ like the value was interpreted as percentage, since it was roughly
        # 10% too large. But I tested that and can now rule that out. Hard coded as 85,
        # for now. @HARDCODED @FIX

        sizes_dict = {cb_active      : (6, 1),
                      txt_name       : (20, 1),
                      txt_head_state : (35, 1),
                      txt_status     : (5, 1),
                      txt_upstream   : (10, 1),
                      combo_tags     : (20, 1),
                      btn_open       : (11, 1),
                      pb_repo_action : (85, 1)}

        return sizes_dict

    def test_function(self, index, repo):
        print('Testfunction: {} {}'.format(index, repo))
        return [[]]


    def layout_repo_table(self, path):
        """ Generates layout for table """

        sizes = self.table_sizes_dict()

        layout = [[gui.Text('Include', size=sizes[cb_active]),
                   gui.Text('Repository', size=sizes[txt_name]),
                   gui.Text('HEAD', size=sizes[txt_head_state]),
                   gui.Text('Status', size=sizes[txt_status]),
                   gui.Text('Upstream', size=sizes[txt_upstream]),
                   gui.Text('Tags', size=sizes[combo_tags]),
                   gui.Text('Filebrowser', size=sizes[btn_open])
                  ]]

        # Ignore the pooling completely, if we are limited to one core anyway.
        if (self.cpu_count > 1):
            with Pool(processes=self.cpu_count) as pool:
                layout_rows = list(pool.map(lambda e: self.table_row_layout_for_repo(e[0], e[1]),
                                            enumerate(self.repos)))
        else:
            layout_rows = list(map(lambda e: self.table_row_layout_for_repo(e[0], e[1]),
                                   enumerate(self.repos)))

        # Unwrap the inner lists
        # TODO: After an hour of debugging this was a working solution. A quick quess is, that the
        # list(...) function call wraps the lists another time. In this case I would have expected a
        # _single_ inner list which I could unwrap: [layout_rows] = list(map(...)). I can't though.
        # Fix if you have time to spare. For now take this "temporary" solution.

        for n in layout_rows:
            layout = layout + n

        print('\n'.format(layout))
        return layout


    def table_row_layout_for_repo(self, index, repo):

        name = self.git.get_repo_name(repo)

        status_color     = 'black'
        upstream_color   = 'black'
        head_state_color = 'black'

        if (self.git.is_dirty(repo)):
            status       = 'Dirty'
            status_color = color_highlight

        else:
            status = 'Clean'

        # Name of current branch
        branch = '{}'.format(self.git.active_branch(repo))

        # Description of Head State
        head_state = '{}'.format(self.git.head_state(repo))

        if (repo.head.is_detached):
            head_state_color = color_highlight

        # Set to -1 so that we can distinguish if this value has been updated
        behind = -1

        # CHECK IF BRANCH IS NONE!!
        print('Dis none? {}'.format(branch))
        print(name)
        print(repo.remotes)
        print('Current Branch: {}'.format(branch))
        print('Current Headstate: {}'.format(head_state))

        if (branch in repo.branches):
            if (len(repo.remotes) > 0):
                for r in repo.remotes:
                    if r.name == 'origin':
                        behind = self.git.behind_branch(repo, 'origin', branch)
                        break

        if (behind == -1):
            upstream = 'n/a'

        elif (behind == 0):
            upstream = 'Up to date'

        else:
            upstream = "{} behind".format(behind)
            upstream_color = color_highlight

        tags = [t.path.lstrip('refs/tags/') for t in repo.tags]
        no_tags_available = (len(tags) == 0)

        if (no_tags_available):
            tags.append('No Tags')
        else:
            tags.sort(reverse=True)

        repo_path = self.git.get_root(repo)

        sizes = self.table_sizes_dict()

        layout = [[gui.CBox('',
                            default=True,
                            size=sizes[cb_active],
                            key='{}{}'.format(index, cb_active)),

                   gui.Text('{}'.format(name),
                            font='Helvetica 10 bold',
                            size=sizes[txt_name],
                            key='{}{}'.format(index, txt_name)),

                   gui.Text('{}'.format(head_state),
                            text_color=head_state_color,
                            size=sizes[txt_head_state],
                            key='{}{}'.format(index, txt_head_state)),

                   gui.Text('{}'.format(status),
                            text_color=status_color,
                            size=sizes[txt_status],
                            key='{}{}'.format(index, txt_status)),

                   gui.Text('{}'.format(upstream),
                            text_color=upstream_color,
                            size=sizes[txt_upstream],
                            key='{}{}'.format(index, txt_upstream)),

                   gui.InputCombo(tags,
                                  size=sizes[combo_tags],
                                  key='{}{}'.format(index, combo_tags),
                                  disabled=no_tags_available),

                   gui.Button('Open',
                              size=sizes[btn_open],
                              tooltip='Open in Filebrowser',
                              key='{}{}'.format(index, btn_open))],

                  [gui.ProgressBar(100,
                                   orientation='h',
                                   size=sizes[pb_repo_action],
                                   bar_color=(color_accent, 'white'),
                                   border_width=0,
                                   key='{}{}'.format(index, pb_repo_action))]
        ]

        return layout


    def assign_values(self, values):
        """ Takes the gui loop values and updates the instance variables """

        ##
        # Only _editable_ text elements return a value!
        try:
            # Assign Checkboxes
            self.should_autostash = values[cb_autostash]
            self.should_prune     = values[cb_prune]
            self.should_log       = values[cb_log]
            self.is_verbose       = values[cb_verbose]
            self.is_confirmed     = values[cb_confirmation]

            # Assign input fields
            self.destination_dir      = values[txt_destination_dir]
            self.extraction_command   = values[txt_extraction_command]
            self.extraction_tag       = values[txt_extraction_tag]
            self.extraction_directory = values[txt_extraction_directory]


            for idx in range(0, len(self.repos)):
                # TODO: Assign. GUI layout is generated in parallel, do NOT
                # assume the order to be the same as in self.repos!
                active = values['{}{}'.format(idx, cb_active)]

        except KeyError as error:
            print(error)


    def create_window(self):
        """ Setup GUI layout and start loop """


        main_layout = [[gui.Text('Containing Folder',
                            size=(15, 1)),
                   gui.FolderBrowse(target=txt_containing_dir, key=btn_folderbrowse),
                   gui.Text('{}'.format(self.path), key=txt_containing_dir)]

                  # ,[gui.Text('Destination Folder',
                  #           size=(15, 1)),
                  #  gui.FolderBrowse(target=txt_destination_dir),
                  #  gui.Text('{}/TagSnag'.format(self.path), key=txt_destination_dir)]
                  ]
        # Spacer
        spacer = [[gui.Text('_' * 133)]]

        main_layout = main_layout + spacer
        table_layout = self.layout_repo_table(self.path)

        main_layout = main_layout + table_layout

        # print('\n'.join(str(line) for line in self.layout_repo_table(self.path)))
        main_layout = main_layout + spacer

        main_layout = main_layout + [

            [gui.Button('Invert Selection', key=btn_invert_selection),
             gui.CBox('Autostash', default=True, key=cb_autostash),
             gui.CBox('Prune', default=True, key=cb_prune),
             gui.CBox('Log', default=False, key=cb_log),
             gui.CBox('Verbose', default=False, key=cb_verbose),
             gui.Button('Update', key=btn_update)],

            [gui.Input(default_text='git stash', size=(70,1), disabled=True, key=txt_git_command),
             gui.Button('Execute for selection', disabled=True, key=btn_execute),
             gui.CBox('I know what I\'m doing...', default=False, key=cb_confirmation)],

            [gui.Input(default_text='Tag', size=(20,1), key=txt_git_tag),
             gui.Input(default_text='Directory', size=(30,1), key=txt_git_directory),
             gui.Input(default_text='Destination', size=(30,1), key=txt_git_destination),
             gui.Button('Dry Run', key=btn_dryrun),
             gui.Button('Extract', disabled=True, key=btn_extract)],

            [gui.Button('Exit', key=btn_exit),
             gui.Button('Contact', key=btn_contact)]]

        log_layout = [[gui.Output(size=(200, 100))]]

        tab_layout = [[gui.TabGroup([[gui.Tab('Main', main_layout), gui.Tab('Log', log_layout)]])]]

        window = gui.Window('TagSnag').Layout(tab_layout)

        # GUI Event Loop
        while True:
            event, values = window.Read(timeout=10)
            self.assign_values(values)
            if event != gui.TIMEOUT_KEY:
                # window.Element('_MULTIOUT_').Update(str(event) + '\n' + str(values), append=True)
                window.FindElement('__0_PROGBAR__').UpdateBar(50 + 1)
                window.FindElement('__1_PROGBAR__').UpdateBar(50 + 1)
                print(event, values)

            if event is None or event == 'Exit':
                break

            if event == 'Load':
                # window.FindElement('_DESTINATION_FOLDER_').Update(val
                print('TODO: LOAD DIRECTORY:')

            if event == 'Show':
                # change the "output" element to be the value of "input" element  
                window.FindElement('_OUTPUT_').Update(values['_IN_'])

        window.Close()
