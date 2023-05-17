from django.shortcuts import render, redirect
import calendar
from calendar import HTMLCalendar
from datetime import datetime
from django.http import HttpResponseRedirect
from .models import Event, Venue
# Import User Model From Django
from django.contrib.auth.models import User
from .forms import VenueForm, EventForm, EventFormAdmin, MyForm, MyForm2, Search
from django.http import HttpResponse
import csv
from django.contrib import messages

# Import PDF Stuff
from django.http import FileResponse
import io
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch
from reportlab.lib.pagesizes import letter
from django.db.models import Q

# Import Pagination Stuff
from django.core.paginator import Paginator

# def specific(request):
# 	if request.method == "POST":
# 		form = MyForm(request.POST)
# 		if form.is_valid():
# 			field_date = form.cleaned_data['date_field']
# 			# create a calendar
# 			cal = HTMLCalendar().formatmonth(
# 				field_date,
# 				)
# 			# Get current year
# 			now = datetime.now()
# 			current_year = now.year
# 			# Query the Events Model For Dates
# 			event_list = Event.objects.filter(
# 				event_date__year = field_date.year,
# 				event_date__month = field_date.month
# 				)
# 			return render(request, 
# 				'events/home.html', {
# 				"year": field_date.year,
# 				"month": field_date.month,
# 				"cal": cal,
# 				"current_year": current_year,
# 				"event_list": event_list,
# 				"form": form
# 				})
			
# Show Event
def show_event(request, event_id):
	event = Event.objects.get(pk=event_id)
	return render(request, 'events/show_event.html', {
			"event":event
			})

# Show Events In A Venue
def venue_events(request, venue_id):
	# Grab the venue
	venue = Venue.objects.get(id=venue_id)	
	# Grab the events from that venue
	events = venue.event_set.all()
	if events:
		return render(request, 'events/venue_events.html', {
			"events":events
			})
	else:
		messages.success(request, ("That Venue Has No Events At This Time..."))
		return redirect('admin_approval')


# Create Admin Event Approval Page
def admin_approval(request):
	# Get The Venues
	venue_list = Venue.objects.all()
	# Get Counts
	event_count = Event.objects.all().count()
	venue_count = Venue.objects.all().count()
	user_count = User.objects.all().count()

	event_list = Event.objects.all().order_by('-event_date')
	if request.user.is_superuser:
		if request.method == "POST":
			# Get list of checked box id's
			id_list = request.POST.getlist('boxes')

			# Uncheck all events
			event_list.update(approved=False)

			# Update the database
			for x in id_list:
				Event.objects.filter(pk=int(x)).update(approved=True)
			
			# Show Success Message and Redirect
			messages.success(request, ("Event List Approval Has Been Updated!"))
			return redirect('list-events')



		else:
			return render(request, 'events/admin_approval.html',
				{"event_list": event_list,
				"event_count":event_count,
				"venue_count":venue_count,
				"user_count":user_count,
				"venue_list":venue_list})
	else:
		messages.success(request, ("You aren't authorized to view this page!"))
		return redirect('home')


# Create My Events Page
def my_events(request):
	if request.user.is_authenticated:
		me = request.user.id
		events = Event.objects.filter(attendees=me)
		return render(request, 
			'events/my_events.html', {
				"events":events
			})

	else:
		messages.success(request, ("You Aren't Authorized To View This Page"))
		return redirect('home')

# Generate a PDF File Venue List
def venue_pdf(request):
	# Create Bytestream buffer
	buf = io.BytesIO()
	# Create a canvas
	c = canvas.Canvas(buf, pagesize=letter, bottomup=0)
	# Create a text object
	textob = c.beginText()
	textob.setTextOrigin(inch, inch)
	textob.setFont("Helvetica", 14)

	# Add some lines of text
	#lines = [
	#	"This is line 1",
	#	"This is line 2",
	#	"This is line 3",
	#]
	
	# Designate The Model
	venues = Venue.objects.all()

	# Create blank list
	lines = []

	for venue in venues:
		lines.append(venue.name)
		lines.append(venue.address)
		lines.append(venue.zip_code)
		lines.append(venue.phone)
		lines.append(venue.web)
		lines.append(venue.email_address)
		lines.append(" ")

	# Loop
	for line in lines:
		textob.textLine(line)

	# Finish Up
	c.drawText(textob)
	c.showPage()
	c.save()
	buf.seek(0)

	# Return something
	return FileResponse(buf, as_attachment=True, filename='venue.pdf')

# Generate CSV File Venue List
def venue_csv(request):
	response = HttpResponse(content_type='text/csv')
	response['Content-Disposition'] = 'attachment; filename=venues.csv'
	
	# Create a csv writer
	writer = csv.writer(response)

	# Designate The Model
	venues = Venue.objects.all()

	# Add column headings to the csv file
	writer.writerow(['Venue Name', 'Address', 'Zip Code', 'Phone', 'Web Address', 'Email'])

	# Loop Thu and output
	for venue in venues:
		writer.writerow([venue.name, venue.address, venue.zip_code, venue.phone, venue.web, venue.email_address])

	return response



# Generate Text File Venue List
def venue_text(request):
	response = HttpResponse(content_type='text/plain')
	response['Content-Disposition'] = 'attachment; filename=venues.txt'
	# Designate The Model
	venues = Venue.objects.all()

	# Create blank list
	lines = []
	# Loop Thu and output
	for venue in venues:
		lines.append(f'{venue.name}\n{venue.address}\n{venue.zip_code}\n{venue.phone}\n{venue.web}\n{venue.email_address}\n\n\n')

	#lines = ["This is line 1\n", 
	#"This is line 2\n",
	#"This is line 3\n\n",
	#"John Elder Is Awesome!\n"]

	# Write To TextFile
	response.writelines(lines)
	return response

# Delete a Venue
def delete_venue(request, venue_id):
	venue = Venue.objects.get(pk=venue_id)
	venue.delete()
	return redirect('list-venues')		


# Delete an Event
def delete_event(request, event_id):
	event = Event.objects.get(pk=event_id)
	if request.user == event.manager:
		event.delete()
		messages.success(request, ("Event Deleted!!"))
		return redirect('list-events')		
	else:
		messages.success(request, ("You Aren't Authorized To Delete This Event!"))
		return redirect('list-events')		

def add_event(request):
	submitted = False
	if request.method == "POST":
		if request.user.is_superuser:
			form = EventFormAdmin(request.POST, request.FILES)
			if form.is_valid():
				event = form.save(commit=False)
				event.manager = request.user
				# files = request.FILES.getlist('files')
				# for file in files:
				# 	event.files = file
				event.save()
				return 	HttpResponseRedirect('/add_event?submitted=True')	
		else:
			form = EventForm(request.POST, request.FILES)
			if form.is_valid():
				#form.save()
				event = form.save(commit=False)
				event.manager = request.user # logged in user
				event.save()
				return 	HttpResponseRedirect('/add_event?submitted=True')	
	else:
		# Just Going To The Page, Not Submitting 
		if request.user.is_superuser:
			form = EventFormAdmin
		else:
			form = EventForm

		if 'submitted' in request.GET:
			submitted = True

	return render(request, 'events/add_event.html', {'form':form, 'submitted':submitted})


def update_event(request, event_id):
	event = Event.objects.get(pk=event_id)
	if request.user.is_superuser:
		form = EventFormAdmin(request.POST or None, instance=event)	
	else:
		form = EventForm(request.POST or None, instance=event)
	
	if form.is_valid():
		form.save()
		return redirect('list-events')

	return render(request, 'events/update_event.html', 
		{'event': event,
		'form':form})


def update_venue(request, venue_id):
	venue = Venue.objects.get(pk=venue_id)
	form = VenueForm(request.POST or None, request.FILES or None, instance=venue)
	if form.is_valid():
		form.save()
		return redirect('list-venues')

	return render(request, 'events/update_venue.html', 
		{'venue': venue,
		'form':form})

def search_venues(request):
	if request.method == "POST":
		searched = request.POST['searched']
		venues = Venue.objects.filter(name__contains=searched)
	
		return render(request, 
		'events/search_venues.html', 
		{'searched':searched,
		'venues':venues})
	else:
		return render(request, 
		'events/search_venues.html', 
		{})


def search_events(request):
	if request.method == "POST":
		form3 = Search(request.POST)
		if form3.is_valid():
			field_data = form3.cleaned_data['name']
			# events = Event.objects.filter(name__contains=searched)
			events = Event.objects.filter(
				Q(name__contains=field_data) |  # filter by field1 contains searched term
				Q(description__contains=field_data)  # filter by field2 contains searched term (case-insensitive)
				)
			return render(request, 
			'events/search_events.html', 
			{'searched':events,
			'events':events,
			'form3': form3
			})
		else:
			return render(request, 
			'events/search_events.html', 
			{'form3': form3})
	else:
		form3 = Search
		return render(request, 
		'events/search_events.html', 
		{'form3': form3})


def show_venue(request, venue_id):
	venue = Venue.objects.get(pk=venue_id)
	venue_owner = User.objects.get(pk=venue.owner)

	# Grab the events from that venue
	events = venue.event_set.all()

	return render(request, 'events/show_venue.html', 
		{'venue': venue,
		'venue_owner':venue_owner,
		'events':events})

def list_venues(request):
	#venue_list = Venue.objects.all().order_by('?')
	venue_list = Venue.objects.all()

	# Set up Pagination
	p = Paginator(Venue.objects.all(), 3)
	page = request.GET.get('page')
	venues = p.get_page(page)
	nums = "a" * venues.paginator.num_pages
	return render(request, 'events/venue.html', 
		{'venue_list': venue_list,
		'venues': venues,
		'nums':nums}
		)


def add_venue(request):
	submitted = False
	if request.method == "POST":
		form = VenueForm(request.POST, request.FILES)
		if form.is_valid():
			venue = form.save(commit=False)
			venue.owner = request.user.id # logged in user
			venue.save()
			#form.save()
			return 	HttpResponseRedirect('/add_venue?submitted=True')	
	else:
		form = VenueForm
		if 'submitted' in request.GET:
			submitted = True

	return render(request, 'events/add_venue.html', {'form':form, 'submitted':submitted})

def all_events(request):
	event_list = Event.objects.all().order_by('-event_date')
	return render(request, 'events/event_list.html', 
		{'event_list': event_list})


def home(request, year=datetime.now().year, month=datetime.now().strftime('%B') ):
	if request.method == "POST":
		form = MyForm(request.POST)
		formtwo = MyForm2(request.POST)
		if form.is_valid():
			field_date = form.cleaned_data['date_field']
			# Get current year
			now = datetime.now()
			current_year = now.year
			# Query the Events Model For Dates
			event_list = Event.objects.filter(
				event_date__year = field_date.year,
				event_date__month = field_date.month,
				event_date__day = field_date.day
				)
			return render(request, 
				'events/home.html', {
				"year": field_date.year,
				"month": field_date.month,
				"cal": cal,
				"date": field_date,
				"current_year": current_year,
				"event_list": event_list,
				"form": form,
				"form2": formtwo
				})
		elif formtwo.is_valid():
			field_data = formtwo.cleaned_data['month_field']
			# create a calendar
			# Get current year
			now = datetime.now()
			current_year = now.year
			# Query the Events Model For Dates
			event_list = Event.objects.filter(
				event_date__year = year,
				event_date__month = field_data,
				)
			return render(request, 
				'events/home.html', {
				"year": year,
				"month": field_data,
				"current_year": current_year,
				"event_list": event_list,
				"form": form,
				"form2": formtwo
				})
	form = MyForm
	formtwo = MyForm2
	month = month.capitalize()
	# Convert month from name to number
	month_number = list(calendar.month_name).index(month)
	month_number = int(month_number)

	# create a calendar
	cal = HTMLCalendar().formatmonth(
		year, 
		month_number)
	# Get current year
	now = datetime.now()
	current_year = now.year
	
	# Query the Events Model For Dates
	event_list = Event.objects.filter(
		event_date__year = year,
		event_date__month = month_number
		)

	# Get current time
	time = now.strftime('%I:%M %p')
	# if spdate:
	# 	event_list = Event.objects.filter(
	# 		event_date = spdate,
	# 		)
	# 	return render(request, 
	# 		'events/home.html', {
	# 		"name": name,
	# 		"year": year,
	# 		"month": month,
	# 		"month_number": month_number,
	# 		"cal": cal,
	# 		"current_year": current_year,
	# 		"time":time,
	# 		"event_list": event_list,
	# 		"form": form
	# 		})
	
	return render(request, 
		'events/home.html', {
		"year": year,
		"month": month,
		"month_number": month_number,
		"cal": cal,
		"current_year": current_year,
		"time":time,
		"event_list": event_list,
		"form": form,
		"form2": formtwo
		})


