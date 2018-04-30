import sqlite3
import tkinter as tk
from tkinter import ttk

import pygubu

from .components import AutocompleteCombobox
from .state import State, GroupBy, OrderBy
from .utils import data_filepath


class Application:
    def __init__(self):
        self.about_dialog = None

        # SQL connection
        self.db_conn = sqlite3.connect(data_filepath('flightdb.sqlite'))

        # State
        self.state = State(self.db_conn)

        # Build UI
        self.builder = b = pygubu.Builder()
        b.add_from_file(data_filepath('application.ui'))

        self.mainwindow = b.get_object('mainwindow')  # type: tk.Toplevel

        # Results
        self.results_tv = b.get_object('results_tv')  # type: ttk.Treeview
        self.results_scrollbar = b.get_object('results_scrollbar', self.mainwindow)  # type: ttk.Scrollbar
        self.results_found_label = b.get_object('results_found_label')  # type: ttk.Label

        self.results_tv.configure(yscrollcommand=self.results_scrollbar.set)
        self.results_scrollbar.configure(command=self.results_tv.yview)

        # Sort By menu
        self.sort_by_menu_btn = b.get_object('sort_by_menu_btn', self.mainwindow)  # type: tk.Menubutton
        self.sort_by_menu = b.get_object('sort_by_menu', self.mainwindow)  # type: tk.Menu

        # Group By menu
        self.group_by_menu_btn = b.get_object('group_by_menu_btn', self.mainwindow)  # type: tk.Menubutton
        self.group_by_menu = b.get_object('group_by_menu', self.mainwindow)  # type: tk.Menu

        """ Filters """
        self.filter_frame = b.get_object('filter_frame', self.mainwindow)  # type: ttk.Frame

        # Origin
        self.origin_box = b.get_object('origin_box', self.mainwindow)  # type: ttk.Combobox
        self.origin_box.grid_forget()
        self.origin_box = AutocompleteCombobox(self.filter_frame)
        self.origin_box.set_completion_list(self.state.airport_options)
        self.origin_box.grid(row=5, column=0)
        self.origin_box.current(0)
        self.origin_box.bind('<<ComboboxSelected>>', self.on_origin_selection)

        # Destination
        self.dest_box = b.get_object('dest_box', self.mainwindow)  # type: ttk.Combobox
        self.dest_box.grid_forget()
        self.dest_box = AutocompleteCombobox(self.filter_frame)
        self.dest_box.set_completion_list(self.state.airport_options)
        self.dest_box.grid(row=8, column=0)
        self.dest_box.current(0)
        self.dest_box.bind('<<ComboboxSelected>>', self.on_destination_selection)

        # Distance Filter
        self.distance_filter_box = b.get_object('distance_filter_box', self.mainwindow)  # type: ttk.Combobox
        self.distance_filter_box.grid_forget()
        self.distance_filter_box = AutocompleteCombobox(self.filter_frame)
        self.distance_filter_box.set_completion_list(self.state.distance_options)
        self.distance_filter_box.grid(row=11, column=0)
        self.distance_filter_box.current(0)
        self.distance_filter_box.bind('<<ComboboxSelected>>', self.on_distance_selection)

        # Connect to Delete event
        self.mainwindow.protocol("WM_DELETE_WINDOW", self.quit)

        # Callbacks
        b.connect_callbacks(self)

        # Execute query
        self.execute_query()

    def quit(self, event=None):
        self.mainwindow.quit()

    def run(self):
        self.mainwindow.mainloop()

    def on_sort_by_menu_action(self, option_id=None):
        """
        Triggered when sort_by_menu is changed
        :param option_id: id of option picked
        """
        if option_id == 'sm_seats_transported_desc':
            self.sort_by_menu_btn['text'] = 'Sort By Seats Transported (DESC)'
            self.state.order_by = OrderBy.seats_transported
        if option_id == 'sm_open_seats_desc':
            self.sort_by_menu_btn['text'] = 'Sort By Open Seats (DESC)'
            self.state.order_by = OrderBy.open_seats

        self.execute_query()

    def on_group_by_menu_action(self, option_id=None):
        """
        Triggered when group_by_menu is changed
        :param option_id: id of option picked
        """
        if option_id == 'gm_month':
            self.group_by_menu_btn['text'] = 'Month'
            self.state.group_by = GroupBy.month
        if option_id == 'gm_airline':
            self.group_by_menu_btn['text'] = 'Airline'
            self.state.group_by = GroupBy.carrier_name

        self.execute_query()

    def on_origin_selection(self, event=None):
        """
        Triggered when origin filter selected
        :param event: ignored
        """
        self.state.origin = self.origin_box.get()
        self.execute_query()

    def on_destination_selection(self, event=None):
        """
        Triggered when destination filter selected
        :param event: ignored
        """
        self.state.dest = self.dest_box.get()
        self.execute_query()

    def on_distance_selection(self, event=None):
        """
        Triggered when distance filter selected
        :param event: ignored
        """
        self.state.distance = self.distance_filter_box.get()
        self.execute_query()

    def execute_query(self):
        """
        Executes a new query and updates the results
        """
        # Query
        print('Query:')
        print(self.state.get_query_params())
        print()

        results = self.state.get_results()
        self.results_tv.delete(*self.results_tv.get_children())  # Clear Treeview

        # Result column headings
        group_column_index = None
        headings = None
        if self.state.group_by is GroupBy.month:
            group_column_index = 0
            self.results_tv['columns'] = headings = ('Month', 'Seats')
            self.results_tv.heading('Month', text='Month')
            self.results_tv.heading('Seats', text='Seats')
        else:
            group_column_index = 1
            self.results_tv['columns'] = headings = ('Airline', 'Seats')
            self.results_tv.heading('Airline', text='Airline')
            self.results_tv.heading('Seats', text='Seats')

        # Filter out unneeded columns
        order_column_index = None
        if self.state.order_by is OrderBy.seats_transported:
            order_column_index = 2
        else:
            order_column_index = 3

        filtered_results = [(row[group_column_index], row[order_column_index]) for row in results]

        # Insert results
        for row in filtered_results:
            self.results_tv.insert('', tk.END, values=row)

        # Update results count
        if len(filtered_results) != 0:
            self.results_found_label['text'] = '{:d} Results Found'.format(len(filtered_results))
        else:
            self.results_found_label['text'] = 'No Results Found'

        # Log Results
        print('Results:')
        if self.state.group_by is GroupBy.month:
            print('{0[0]:12} {0[1]:>18}'.format(headings))
            for row in filtered_results:
                print('{0[0]:12} {0[1]:>18d}'.format(row))
        else:
            print('{0[0]:60} {0[1]:>18}'.format(headings))
            for row in filtered_results:
                print('{0[0]:60} {0[1]:>18d}'.format(row))
        print()
