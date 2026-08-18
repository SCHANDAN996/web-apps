package com.jsps.parentapp.ui.navigation

import androidx.compose.runtime.Composable
import androidx.navigation.NavType
import androidx.navigation.compose.NavHost
import androidx.navigation.compose.composable
import androidx.navigation.compose.rememberNavController
import androidx.navigation.navArgument
import com.jsps.parentapp.ui.screens.AssignmentScreen
import com.jsps.parentapp.ui.screens.AssistantScreen
import com.jsps.parentapp.ui.screens.AttendanceScreen
import com.jsps.parentapp.ui.screens.CalendarScreen
import com.jsps.parentapp.ui.screens.DashboardScreen
import com.jsps.parentapp.ui.screens.FeeScreen
import com.jsps.parentapp.ui.screens.LeaveScreen
import com.jsps.parentapp.ui.screens.LoginScreen
import com.jsps.parentapp.ui.screens.MessageScreen
import com.jsps.parentapp.ui.screens.NotificationScreen
import com.jsps.parentapp.ui.screens.ResultScreen
import com.jsps.parentapp.ui.screens.TransportScreen
import com.jsps.parentapp.ui.viewmodels.ParentViewModel

@Composable
fun AppNavigation(viewModel: ParentViewModel) {
    val navController = rememberNavController()

    NavHost(navController = navController, startDestination = "login") {
        
        composable("login") {
            LoginScreen(
                viewModel = viewModel,
                onLoginSuccess = {
                    navController.navigate("dashboard") {
                        popUpTo("login") { inclusive = true }
                    }
                }
            )
        }

        composable("dashboard") {
            DashboardScreen(
                viewModel = viewModel,
                onViewResults = { studentId ->
                    navController.navigate("results/$studentId")
                },
                onViewAssignments = { className ->
                    navController.navigate("assignments/$className")
                },
                onViewAttendance = { studentId -> navController.navigate("attendance/$studentId") },
                onViewFees = { studentId -> navController.navigate("fees/$studentId") },
                onViewLeave = { studentId -> navController.navigate("leave/$studentId") },
                onViewTransport = { studentId -> navController.navigate("transport/$studentId") },
                onViewCalendar = { studentId -> navController.navigate("calendar/$studentId") },
                onViewMessages = { studentId -> navController.navigate("messages/$studentId") },
                onViewNotifications = { navController.navigate("notifications") },
                onAskAssistant = { navController.navigate("assistant") }
            )
        }

        composable(
            route = "results/{studentId}",
            arguments = listOf(navArgument("studentId") { type = NavType.IntType })
        ) { backStackEntry ->
            val studentId = backStackEntry.arguments?.getInt("studentId") ?: 0
            ResultScreen(
                viewModel = viewModel,
                studentId = studentId,
                onBack = { navController.popBackStack() }
            )
        }

        composable(
            route = "assignments/{className}",
            arguments = listOf(navArgument("className") { type = NavType.StringType })
        ) { backStackEntry ->
            val className = backStackEntry.arguments?.getString("className") ?: ""
            AssignmentScreen(
                viewModel = viewModel,
                className = className,
                onBack = { navController.popBackStack() }
            )
        }

        composable(
            route = "attendance/{studentId}",
            arguments = listOf(navArgument("studentId") { type = NavType.IntType })
        ) { backStackEntry ->
            AttendanceScreen(viewModel, backStackEntry.arguments?.getInt("studentId") ?: 0) { navController.popBackStack() }
        }

        composable(
            route = "fees/{studentId}",
            arguments = listOf(navArgument("studentId") { type = NavType.IntType })
        ) { backStackEntry ->
            FeeScreen(viewModel, backStackEntry.arguments?.getInt("studentId") ?: 0) { navController.popBackStack() }
        }

        composable(
            route = "leave/{studentId}",
            arguments = listOf(navArgument("studentId") { type = NavType.IntType })
        ) { backStackEntry ->
            LeaveScreen(viewModel, backStackEntry.arguments?.getInt("studentId") ?: 0) { navController.popBackStack() }
        }

        composable(
            route = "transport/{studentId}",
            arguments = listOf(navArgument("studentId") { type = NavType.IntType })
        ) { backStackEntry ->
            TransportScreen(viewModel, backStackEntry.arguments?.getInt("studentId") ?: 0) { navController.popBackStack() }
        }

        composable(
            route = "calendar/{studentId}",
            arguments = listOf(navArgument("studentId") { type = NavType.IntType })
        ) { backStackEntry ->
            CalendarScreen(viewModel, backStackEntry.arguments?.getInt("studentId") ?: 0) { navController.popBackStack() }
        }

        composable(
            route = "messages/{studentId}",
            arguments = listOf(navArgument("studentId") { type = NavType.IntType })
        ) { backStackEntry ->
            MessageScreen(viewModel, backStackEntry.arguments?.getInt("studentId") ?: 0) { navController.popBackStack() }
        }

        composable("notifications") {
            NotificationScreen(viewModel) { navController.popBackStack() }
        }

        composable("assistant") {
            AssistantScreen(viewModel) { navController.popBackStack() }
        }
    }
}
