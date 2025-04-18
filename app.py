from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from models.user import User
from dotenv import load_dotenv
import os
import json
from datetime import datetime
from functools import wraps

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'your-secret-key-here')

# Initialize Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# JSON file paths
PETS_FILE = 'data/pets.json'
BREEDS_FILE = 'data/breeds.json'

# Admin credentials
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "admin123"

# Admin login required decorator
def admin_login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'admin_logged_in' not in session:
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)
    return decorated_function

def load_pets():
    if os.path.exists(PETS_FILE):
        with open(PETS_FILE, 'r') as f:
            return json.load(f)
    return {"pets": []}

def save_pets(pets_data):
    with open(PETS_FILE, 'w') as f:
        json.dump(pets_data, f, indent=4)

def load_breeds():
    if os.path.exists(BREEDS_FILE):
        with open(BREEDS_FILE, 'r') as f:
            return json.load(f)
    return {"breeds": []}

def load_breed_activities():
    try:
        with open('data/breed_activities.json', 'r') as f:
            data = json.load(f)
            return data.get('breed_activities', {})
    except FileNotFoundError:
        app.logger.error("breed_activities.json file not found")
        return {}
    except json.JSONDecodeError:
        app.logger.error("Invalid JSON in breed_activities.json")
        return {}
    except Exception as e:
        app.logger.error(f"Error loading breed activities: {str(e)}")
        return {}

@login_manager.user_loader
def load_user(user_id):
    try:
        with open('data/users.json', 'r') as f:
            data = json.load(f)
            for user_data in data['users']:
                if user_data['email'] == user_id:  # Using email as user_id
                    return User.from_dict(user_data)
    except FileNotFoundError:
        return None
    return None

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        user = User.get_by_email(email)
        
        if user:
            if not user.is_active:
                flash('Your account is inactive. Please contact the administrator.', 'error')
                return render_template('auth/login.html')
            
            if user.check_password(password):
                login_user(user)
                flash('Logged in successfully!', 'success')
                return redirect(url_for('dashboard'))
            else:
                flash('Invalid password', 'error')
        else:
            flash('Email not found', 'error')
    
    return render_template('auth/login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        if password != confirm_password:
            flash('Passwords do not match', 'error')
            return render_template('auth/register.html')
        
        if User.get_by_email(email):
            flash('Email already registered', 'error')
            return render_template('auth/register.html')
        
        # Create new user
        user = User(email=email, name=name)
        user.set_password(password)
        User.save_user(user)
        
        flash('Registration successful! Please login.', 'success')
        return redirect(url_for('login'))
    
    return render_template('auth/register.html')

@app.route('/logout')
@login_required
def logout():
    try:
        logout_user()
        session.clear()  # Clear all session data
        flash('You have been successfully logged out.', 'success')
        return redirect(url_for('login'))
    except Exception as e:
        flash('An error occurred while logging out.', 'error')
        return redirect(url_for('dashboard'))

@app.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form.get('email')
        user = User.get_by_email(email)
        
        if user:
            # Here you would typically send a password reset email
            flash('Password reset instructions have been sent to your email.', 'success')
        else:
            flash('Email not found.', 'error')
        
        return redirect(url_for('login'))
    
    return render_template('auth/forgot_password.html')

@app.route('/dashboard')
@login_required
def dashboard():
    try:
        with open('data/pets.json', 'r') as f:
            data = json.load(f)
            # Filter pets for current user by email
            user_pets = [pet for pet in data['pets'] if pet.get('user_email') == current_user.email]
            print("User pets:", user_pets)  # Debug log
    except FileNotFoundError:
        user_pets = []
    
    # Load breed activities
    try:
        with open('data/breed_activities.json', 'r') as f:
            breed_activities = json.load(f)
            print("Loaded breed activities:", breed_activities)  # Debug log
            print("Available breeds:", list(breed_activities.get('breed_activities', {}).keys()))  # Debug log
    except FileNotFoundError:
        breed_activities = {}
    
    # Load medical schedules
    try:
        with open('data/medical_schedules.json', 'r') as f:
            medical_schedules = json.load(f)
    except FileNotFoundError:
        medical_schedules = {'schedules': {}}
    
    return render_template('dashboard.html', 
                         pets=user_pets,
                         breed_activities=breed_activities.get('breed_activities', {}),
                         medical_schedules=medical_schedules)

@app.route('/api/breeds')
def get_breeds():
    return jsonify(load_breeds())

@app.route('/api/pets', methods=['POST'])
@login_required
def add_pet():
    try:
        data = request.get_json()
        
        # Validate required fields
        if not data.get('name'):
            return jsonify({'error': 'Pet name is required'}), 400
        if not data.get('age'):
            return jsonify({'error': 'Pet age is required'}), 400
        if not data.get('breed'):
            return jsonify({'error': 'Pet breed is required'}), 400
            
        # Validate age is a positive number
        try:
            age = float(data.get('age'))
            if age <= 0:
                return jsonify({'error': 'Pet age must be a positive number'}), 400
        except ValueError:
            return jsonify({'error': 'Invalid age format'}), 400

        # Validate breed
        breeds = load_breeds()['breeds']
        if data.get('breed') not in breeds:
            return jsonify({'error': 'Invalid breed selected'}), 400

        pet_data = {
            'id': str(datetime.utcnow().timestamp()),  # Simple unique ID
            'user_email': current_user.email,  # Use email instead of user_id
            'name': data.get('name'),
            'age': data.get('age'),
            'weight': data.get('weight'),
            'breed': data.get('breed'),
            'created_at': datetime.utcnow().isoformat()
        }
            
        # Load current pets and add new pet
        pets_data = load_pets()
        pets_data['pets'].append(pet_data)
        save_pets(pets_data)
        
        return jsonify({'message': 'Pet added successfully'}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/breed-activities')
@login_required
def get_breed_activities():
    try:
        breed_activities = load_breed_activities()
        if not breed_activities:
            return jsonify({'error': 'No breed activities found'}), 404
        return jsonify(breed_activities)
    except Exception as e:
        app.logger.error(f"Error loading breed activities: {str(e)}")
        return jsonify({'error': 'Failed to load breed activities'}), 500

@app.route('/api/pets', methods=['PUT'])
@login_required
def update_pet():
    try:
        data = request.get_json()
        if not data or 'id' not in data:
            return jsonify({'error': 'Pet ID is required'}), 400

        # Load current pets data
        pets_data = load_pets()
        if not pets_data or 'pets' not in pets_data:
            return jsonify({'error': 'No pets found'}), 404

        # Find the pet to update
        pet_id = data['id']
        pet_found = False
        
        for pet in pets_data['pets']:
            if pet['id'] == pet_id:
                # Validate age if provided
                if 'age' in data:
                    try:
                        age = float(data['age'])
                        if age <= 0:
                            return jsonify({'error': 'Pet age must be a positive number'}), 400
                    except ValueError:
                        return jsonify({'error': 'Invalid age format'}), 400

                # Validate breed if provided
                if 'breed' in data:
                    breeds = load_breeds()['breeds']
                    if data['breed'] not in breeds:
                        return jsonify({'error': 'Invalid breed selected'}), 400

                # Update pet details
                pet.update({
                    'name': data.get('name', pet['name']),
                    'age': data.get('age', pet['age']),
                    'breed': data.get('breed', pet['breed']),
                    'weight': data.get('weight', pet['weight']),
                    'updated_at': datetime.utcnow().isoformat()
                })
                pet_found = True
                break

        if not pet_found:
            return jsonify({'error': 'Pet not found'}), 404

        # Save updated pets data
        save_pets(pets_data)
        
        return jsonify({
            'message': 'Pet updated successfully',
            'pet': next(pet for pet in pets_data['pets'] if pet['id'] == pet_id)
        })

    except Exception as e:
        app.logger.error(f'Error updating pet: {str(e)}')
        return jsonify({'error': 'Failed to update pet'}), 500

def save_pets(pets):
    """Save pets data to JSON file"""
    try:
        with open('data/pets.json', 'w') as f:
            json.dump(pets, f, indent=4)
    except Exception as e:
        app.logger.error(f'Error saving pets data: {str(e)}')
        raise

@app.route('/api/breed-recommendations/<breed>')
@login_required
def get_breed_recommendations(breed):
    try:
        # Load breed-specific recommendations
        with open('data/breed_recommendations.json', 'r') as f:
            recommendations = json.load(f)
            
        # Get recommendations for the breed or use default
        breed_data = recommendations.get(breed, recommendations.get('Other', {}))
        
        return jsonify({
            'vaccinations': breed_data.get('vaccinations', []),
            'grooming': breed_data.get('grooming', [])
        })
    except FileNotFoundError:
        return jsonify({
            'error': 'Recommendations not found'
        }), 404
    except Exception as e:
        app.logger.error(f'Error loading breed recommendations: {str(e)}')
        return jsonify({
            'error': 'Failed to load recommendations'
        }), 500

@app.route('/api/schedule-checkup', methods=['POST'])
@login_required
def schedule_checkup():
    try:
        data = request.get_json()
        if not data or not data.get('type') or not data.get('date'):
            return jsonify({'error': 'Missing required fields'}), 400

        # Create checkup record
        checkup_data = {
            'id': str(datetime.utcnow().timestamp()),
            'type': data['type'],
            'date': data['date'],
            'notes': data.get('notes', ''),
            'status': 'scheduled',
            'created_at': datetime.utcnow().isoformat()
        }

        # Load existing schedules or create new structure
        try:
            with open('data/medical_schedules.json', 'r') as f:
                schedules_data = json.load(f)
        except FileNotFoundError:
            schedules_data = {'schedules': {}}

        # Initialize user's schedule list if it doesn't exist
        if current_user.email not in schedules_data['schedules']:
            schedules_data['schedules'][current_user.email] = []

        # Add new schedule
        schedules_data['schedules'][current_user.email].append(checkup_data)

        # Save updated schedules
        with open('data/medical_schedules.json', 'w') as f:
            json.dump(schedules_data, f, indent=4)

        return jsonify({
            'success': True,
            'message': 'Checkup scheduled successfully',
            'schedule': checkup_data
        })

    except Exception as e:
        app.logger.error(f'Error scheduling checkup: {str(e)}')
        return jsonify({'error': 'Failed to schedule checkup'}), 500

@app.route('/api/medical-schedules')
@login_required
def get_medical_schedules():
    try:
        # Load medical schedules
        with open('data/medical_schedules.json', 'r') as f:
            schedules_data = json.load(f)
            
        # Get schedules for current user
        user_schedules = schedules_data['schedules'].get(current_user.email, [])
        
        return jsonify({
            'schedules': user_schedules
        })
    except FileNotFoundError:
        return jsonify({
            'schedules': []
        })
    except Exception as e:
        app.logger.error(f'Error loading medical schedules: {str(e)}')
        return jsonify({
            'error': 'Failed to load medical schedules'
        }), 500

@app.route('/api/medical-schedules/<schedule_id>', methods=['DELETE'])
@login_required
def delete_schedule(schedule_id):
    try:
        # Load medical schedules
        with open('data/medical_schedules.json', 'r') as f:
            schedules_data = json.load(f)
            
        # Get user's schedules
        user_schedules = schedules_data['schedules'].get(current_user.email, [])
        
        # Find and remove the schedule
        user_schedules = [s for s in user_schedules if s['id'] != schedule_id]
        
        # Update the schedules data
        schedules_data['schedules'][current_user.email] = user_schedules
        
        # Save updated schedules
        with open('data/medical_schedules.json', 'w') as f:
            json.dump(schedules_data, f, indent=4)
            
        return jsonify({
            'success': True,
            'message': 'Schedule deleted successfully'
        })
    except Exception as e:
        app.logger.error(f'Error deleting schedule: {str(e)}')
        return jsonify({
            'error': 'Failed to delete schedule'
        }), 500

@app.route('/api/medical-schedules/<schedule_id>/status', methods=['PUT'])
@login_required
def update_schedule_status(schedule_id):
    try:
        data = request.get_json()
        if not data or 'status' not in data:
            return jsonify({'error': 'Missing status field'}), 400
            
        new_status = data['status']
        if new_status not in ['scheduled', 'completed', 'cancelled']:
            return jsonify({'error': 'Invalid status'}), 400

        # Load medical schedules
        with open('data/medical_schedules.json', 'r') as f:
            schedules_data = json.load(f)
            
        # Get user's schedules
        user_schedules = schedules_data['schedules'].get(current_user.email, [])
        
        # Find and update the schedule
        for schedule in user_schedules:
            if schedule['id'] == schedule_id:
                schedule['status'] = new_status
                break
        
        # Update the schedules data
        schedules_data['schedules'][current_user.email] = user_schedules
        
        # Save updated schedules
        with open('data/medical_schedules.json', 'w') as f:
            json.dump(schedules_data, f, indent=4)
            
        return jsonify({
            'success': True,
            'message': 'Schedule status updated successfully'
        })
    except Exception as e:
        app.logger.error(f'Error updating schedule status: {str(e)}')
        return jsonify({
            'error': 'Failed to update schedule status'
        }), 500

@app.route('/api/breed-nutrition/<breed>')
def get_breed_nutrition(breed):
    try:
        # Convert breed name to title case for consistent matching
        breed = breed.title()
        app.logger.info(f"Fetching nutrition data for breed: {breed}")
        
        with open('data/breed_nutrition.json', 'r') as f:
            nutrition_data = json.load(f)
            
        if breed not in nutrition_data:
            app.logger.warning(f"Breed not found in nutrition data: {breed}")
            # Try to find a close match
            close_matches = [b for b in nutrition_data.keys() if breed.lower() in b.lower()]
            if close_matches:
                app.logger.info(f"Found close match: {close_matches[0]}")
                return jsonify(nutrition_data[close_matches[0]])
            
            # If no close match found, use the "Other" category
            app.logger.info(f"Using 'Other' category for breed: {breed}")
            return jsonify(nutrition_data.get("Other", {
                "error": "No nutrition data available"
            }))
            
        app.logger.info(f"Successfully found nutrition data for {breed}")
        return jsonify(nutrition_data[breed])
        
    except FileNotFoundError:
        app.logger.error("breed_nutrition.json file not found")
        return jsonify({"error": "Nutrition data file not found"}), 500
    except json.JSONDecodeError:
        app.logger.error("Error decoding breed_nutrition.json")
        return jsonify({"error": "Invalid nutrition data format"}), 500
    except Exception as e:
        app.logger.error(f"Error in get_breed_nutrition: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

# Product routes
@app.route('/api/products')
def get_products():
    try:
        with open('data/products.json', 'r') as f:
            data = json.load(f)
            return jsonify(data['products'])
    except Exception as e:
        app.logger.error(f"Error loading products: {str(e)}")
        return jsonify({"error": "Failed to load products"}), 500

@app.route('/api/products/<int:product_id>')
def get_product(product_id):
    try:
        with open('data/products.json', 'r') as f:
            data = json.load(f)
            product = next((p for p in data['products'] if p['id'] == product_id), None)
            if product:
                return jsonify(product)
            return jsonify({"error": "Product not found"}), 404
    except Exception as e:
        app.logger.error(f"Error loading product {product_id}: {str(e)}")
        return jsonify({"error": "Failed to load product"}), 500

@app.route('/api/products/category/<category>')
def get_products_by_category(category):
    try:
        with open('data/products.json', 'r') as f:
            data = json.load(f)
            if category.lower() == 'all':
                return jsonify(data['products'])
            filtered_products = [p for p in data['products'] if p['category'].lower() == category.lower()]
            return jsonify(filtered_products)
    except Exception as e:
        app.logger.error(f"Error loading products for category {category}: {str(e)}")
        return jsonify({"error": "Failed to load products"}), 500

@app.route('/api/products/search')
def search_products():
    query = request.args.get('q', '').lower()
    try:
        with open('data/products.json', 'r') as f:
            data = json.load(f)
            if not query:
                return jsonify(data['products'])
            filtered_products = [
                p for p in data['products']
                if query in p['name'].lower() or
                   query in p['description'].lower() or
                   query in p['category'].lower()
            ]
            return jsonify(filtered_products)
    except Exception as e:
        app.logger.error(f"Error searching products: {str(e)}")
        return jsonify({"error": "Failed to search products"}), 500

# Cart routes
@app.route('/api/cart', methods=['POST'])
def add_to_cart():
    if 'cart' not in session:
        session['cart'] = []
    
    data = request.get_json()
    product_id = data.get('product_id')
    quantity = data.get('quantity', 1)
    
    try:
        with open('data/products.json', 'r') as f:
            products_data = json.load(f)
            product = next((p for p in products_data['products'] if p['id'] == product_id), None)
            
            if not product:
                return jsonify({"error": "Product not found"}), 404
            
            cart_item = next((item for item in session['cart'] if item['id'] == product_id), None)
            
            if cart_item:
                cart_item['quantity'] += quantity
            else:
                session['cart'].append({
                    'id': product_id,
                    'name': product['name'],
                    'price': product['price'],
                    'image': product['image'],
                    'quantity': quantity
                })
            
            session.modified = True
            return jsonify({"message": "Product added to cart", "cart": session['cart']})
    except Exception as e:
        app.logger.error(f"Error adding to cart: {str(e)}")
        return jsonify({"error": "Failed to add product to cart"}), 500

@app.route('/api/cart', methods=['GET'])
def get_cart():
    cart = session.get('cart', [])
    return jsonify(cart)

@app.route('/api/cart/<int:product_id>', methods=['DELETE'])
def remove_from_cart(product_id):
    if 'cart' not in session:
        return jsonify({"error": "Cart is empty"}), 404
    
    cart = session['cart']
    session['cart'] = [item for item in cart if item['id'] != product_id]
    session.modified = True
    
    return jsonify({"message": "Product removed from cart", "cart": session['cart']})

@app.route('/api/cart/clear', methods=['POST'])
def clear_cart():
    session['cart'] = []
    session.modified = True
    return jsonify({"message": "Cart cleared"})

@app.route('/api/bookings', methods=['POST'])
def create_booking():
    try:
        booking_data = request.json
        
        # Load existing bookings
        with open('data/booked.json', 'r') as f:
            bookings = json.load(f)
        
        # Generate a new booking ID
        last_id = int(bookings['bookings'][-1]['booking_id'].replace('B', '')) if bookings['bookings'] else 0
        new_id = f"B{str(last_id + 1).zfill(3)}"
        
        # Add additional booking details
        booking_data['booking_id'] = new_id
        booking_data['status'] = 'confirmed'
        booking_data['booking_date'] = datetime.now().isoformat()
        
        # Add the new booking
        bookings['bookings'].append(booking_data)
        
        # Save updated bookings
        with open('data/booked.json', 'w') as f:
            json.dump(bookings, f, indent=4)
        
        return jsonify({'success': True, 'booking_id': new_id})
    except Exception as e:
        print(f"Error creating booking: {str(e)}")
        return jsonify({'success': False, 'error': 'Failed to create booking'}), 500

@app.route('/api/bookings', methods=['GET'])
def get_bookings():
    try:
        # Load bookings from file
        with open('data/booked.json', 'r') as f:
            bookings = json.load(f)
            
        # Sort bookings by date (newest first)
        bookings['bookings'].sort(key=lambda x: x['booking_date'], reverse=True)
        
        return jsonify(bookings)
    except Exception as e:
        print(f"Error fetching bookings: {str(e)}")
        return jsonify({'success': False, 'error': 'Failed to fetch bookings'}), 500

@app.route('/api/bookings/user', methods=['GET'])
@login_required
def get_user_bookings():
    try:
        if not current_user.is_authenticated:
            return jsonify({'error': 'User not authenticated'}), 401

        # Load all bookings
        with open('data/booked.json', 'r') as f:
            all_bookings = json.load(f)
        
        # Filter bookings for current user
        user_bookings = {
            'bookings': [
                booking for booking in all_bookings['bookings']
                if booking['customer_details']['email'].lower() == current_user.email.lower()
            ]
        }
        
        return jsonify(user_bookings)
    except Exception as e:
        print(f"Error fetching user bookings: {str(e)}")
        return jsonify({'error': 'Failed to fetch bookings'}), 500

@app.route('/api/change-password', methods=['POST'])
@login_required
def change_password():
    try:
        data = request.get_json()
        current_password = data.get('current_password')
        new_password = data.get('new_password')
        
        if not current_password or not new_password:
            return jsonify({'success': False, 'error': 'Both current and new passwords are required'}), 400
            
        # Verify current password
        if not current_user.check_password(current_password):
            return jsonify({'success': False, 'error': 'Current password is incorrect'}), 401
            
        # Update the user's password
        current_user.set_password(new_password)
        
        # Save updated user data
        try:
            with open('data/users.json', 'r') as f:
                users_data = json.load(f)
                
            # Find and update the user's password
            for user in users_data['users']:
                if user['email'] == current_user.email:
                    user['password_hash'] = current_user.password_hash  # Get the hash from the user object
                    break
                    
            # Save the updated data
            with open('data/users.json', 'w') as f:
                json.dump(users_data, f, indent=4)
                
            return jsonify({'success': True, 'message': 'Password updated successfully'})
            
        except Exception as e:
            print(f"Error saving password: {str(e)}")
            return jsonify({'success': False, 'error': 'Failed to save new password'}), 500
            
    except Exception as e:
        print(f"Error changing password: {str(e)}")
        return jsonify({'success': False, 'error': 'Failed to change password'}), 500

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            session['admin_logged_in'] = True
            return redirect(url_for('admin_dashboard'))
        else:
            flash('Invalid username or password')
            return redirect(url_for('admin_login'))
    
    return render_template('admin_login.html')

@app.route('/admin/dashboard')
@admin_login_required
def admin_dashboard():
    try:
        # Load users from JSON file
        with open('data/users.json', 'r') as f:
            data = json.load(f)
            users = []
            for user_data in data['users']:
                user = {
                    'email': user_data.get('email'),
                    'username': user_data.get('name'),
                    'created_at': datetime.fromisoformat(user_data.get('created_at', datetime.now().isoformat())),
                    'is_active': user_data.get('is_active', True)
                }
                users.append(user)
        return render_template('admin_dashboard.html', users=users)
    except FileNotFoundError:
        return render_template('admin_dashboard.html', users=[])
    except Exception as e:
        flash('Error loading users: ' + str(e))
        return render_template('admin_dashboard.html', users=[])

@app.route('/admin/logout')
def admin_logout():
    session.pop('admin_logged_in', None)
    return redirect(url_for('index'))

@app.route('/admin/users/<email>/delete', methods=['POST'])
@admin_login_required
def delete_user(email):
    try:
        # Load users from JSON file
        with open('data/users.json', 'r') as f:
            data = json.load(f)
        
        # Filter out the user to delete
        data['users'] = [user for user in data['users'] if user.get('email') != email]
        
        # Save updated users list
        with open('data/users.json', 'w') as f:
            json.dump(data, f, indent=4)
            
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/admin/users/<email>/toggle-status', methods=['POST'])
@admin_login_required
def toggle_user_status(email):
    try:
        # Load users from JSON file
        with open('data/users.json', 'r') as f:
            data = json.load(f)
        
        # Find and toggle user status
        user_found = False
        for user in data['users']:
            if user.get('email') == email:
                user['is_active'] = not user.get('is_active', True)
                user_found = True
                break
        
        if not user_found:
            return jsonify({'success': False, 'error': 'User not found'}), 404
        
        # Save updated users list
        with open('data/users.json', 'w') as f:
            json.dump(data, f, indent=4)
            
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/admin/users/<email>/update', methods=['POST'])
@admin_login_required
def update_user(email):
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': 'No data provided'}), 400

        # Load users from JSON file
        with open('data/users.json', 'r') as f:
            users_data = json.load(f)

        # Find and update user
        user_updated = False
        new_email = data.get('email')
        
        # Check if new email already exists (if email is being changed)
        if email != new_email:
            if any(user['email'] == new_email for user in users_data['users']):
                return jsonify({'success': False, 'error': 'Email already exists'}), 400

        for user in users_data['users']:
            if user.get('email') == email:
                # Update only allowed fields
                user['name'] = data.get('username', user['name'])
                user['email'] = new_email
                user_updated = True
                break

        if not user_updated:
            return jsonify({'success': False, 'error': 'User not found'}), 404

        # Save updated users list
        with open('data/users.json', 'w') as f:
            json.dump(users_data, f, indent=4)

        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True, port=5002)