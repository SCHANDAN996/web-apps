import os

def create_file(path, content):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)

base_dir = r"C:\Users\Admin\Desktop\my project\jsps_parent_app"

# Network Layer
api_content = """package com.jsps.parentapp.data.remote

import retrofit2.http.Body
import retrofit2.http.GET
import retrofit2.http.POST
import retrofit2.http.Path

interface JspsApi {
    @POST("api/v1/login")
    suspend fun login(@Body request: LoginRequest): LoginResponse

    @GET("api/v1/parent/{userId}/children")
    suspend fun getChildren(@Path("userId") userId: Int): ChildrenResponse
    
    @GET("api/v1/notices")
    suspend fun getNotices(): NoticesResponse
}
"""

models_content = """package com.jsps.parentapp.data.remote

data class LoginRequest(val username: String, val password: String)
data class LoginResponse(val success: Boolean, val token: String?, val user: User?, val error: String?)
data class User(val id: Int, val name: String, val phone: String)

data class ChildrenResponse(val children: List<Child>)
data class Child(val id: Int, val admission_no: String, val name: String, val class_name: String)

data class NoticesResponse(val notices: List<Notice>)
data class Notice(val id: Int, val title: String, val content: String, val date: String)
"""

# UI Layer
login_screen_content = """package com.jsps.parentapp.ui.screens

import androidx.compose.foundation.layout.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp

@Composable
fun LoginScreen(onLoginSuccess: () -> Unit) {
    var phone by remember { mutableStateOf("") }
    var password by remember { mutableStateOf("") }

    Column(modifier = Modifier.padding(16.dp)) {
        Text(text = "JSPS Parent Portal", style = MaterialTheme.typography.headlineMedium)
        Spacer(modifier = Modifier.height(32.dp))
        
        OutlinedTextField(
            value = phone,
            onValueChange = { phone = it },
            label = { Text("Registered Mobile Number") },
            modifier = Modifier.fillMaxWidth()
        )
        Spacer(modifier = Modifier.height(16.dp))
        
        OutlinedTextField(
            value = password,
            onValueChange = { password = it },
            label = { Text("Password") },
            modifier = Modifier.fillMaxWidth()
        )
        Spacer(modifier = Modifier.height(32.dp))
        
        Button(onClick = onLoginSuccess, modifier = Modifier.fillMaxWidth()) {
            Text("Login")
        }
    }
}
"""

dashboard_screen_content = """package com.jsps.parentapp.ui.screens

import androidx.compose.foundation.layout.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp

@Composable
fun DashboardScreen() {
    Column(modifier = Modifier.padding(16.dp)) {
        Text(text = "Welcome, Parent", style = MaterialTheme.typography.headlineSmall)
        Spacer(modifier = Modifier.height(16.dp))
        
        Card(modifier = Modifier.fillMaxWidth()) {
            Column(modifier = Modifier.padding(16.dp)) {
                Text("Your Children", style = MaterialTheme.typography.titleMedium)
                // List of children will go here
            }
        }
        
        Spacer(modifier = Modifier.height(16.dp))
        
        Card(modifier = Modifier.fillMaxWidth()) {
            Column(modifier = Modifier.padding(16.dp)) {
                Text("Latest Notices", style = MaterialTheme.typography.titleMedium)
                // List of notices will go here
            }
        }
    }
}
"""

# Scaffold
create_file(os.path.join(base_dir, "app/src/main/java/com/jsps/parentapp/data/remote/JspsApi.kt"), api_content)
create_file(os.path.join(base_dir, "app/src/main/java/com/jsps/parentapp/data/remote/Models.kt"), models_content)
create_file(os.path.join(base_dir, "app/src/main/java/com/jsps/parentapp/ui/screens/LoginScreen.kt"), login_screen_content)
create_file(os.path.join(base_dir, "app/src/main/java/com/jsps/parentapp/ui/screens/DashboardScreen.kt"), dashboard_screen_content)

print("Android App Jetpack Compose Structure Scaffolding Complete.")
