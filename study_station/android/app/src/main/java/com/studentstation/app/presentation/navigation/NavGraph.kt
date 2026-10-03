package com.studentstation.app.presentation.navigation

import androidx.compose.animation.*
import androidx.compose.foundation.layout.padding
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.*
import androidx.compose.material.icons.outlined.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.unit.dp
import androidx.navigation.NavDestination.Companion.hierarchy
import androidx.navigation.NavGraph.Companion.findStartDestination
import androidx.navigation.compose.NavHost
import androidx.navigation.compose.composable
import androidx.navigation.compose.currentBackStackEntryAsState
import androidx.navigation.compose.rememberNavController
import com.studentstation.app.R
import com.studentstation.app.presentation.features.dashboard.DashboardScreen
import com.studentstation.app.presentation.features.focus.FocusScreen
import com.studentstation.app.presentation.features.gamification.GamificationScreen
import com.studentstation.app.presentation.features.onboarding.OnboardingScreen
import com.studentstation.app.presentation.features.settings.SettingsScreen
import com.studentstation.app.presentation.features.study.StudyScreen
import com.studentstation.app.presentation.features.study.ContentViewerScreen
import com.studentstation.app.presentation.features.study.StudyPlanScreen
import com.studentstation.app.presentation.features.study.TimetableScreen
import com.studentstation.app.presentation.features.practice.PracticeScreen
import com.studentstation.app.presentation.features.jobs.JobsScreen
import androidx.navigation.NavType
import androidx.navigation.navArgument

/**
 * Navigation Routes
 */
sealed class Screen(
    val route: String,
    val titleRes: Int,
    val selectedIcon: ImageVector,
    val unselectedIcon: ImageVector
) {
    data object Dashboard : Screen("dashboard", R.string.nav_dashboard, Icons.Filled.Dashboard, Icons.Outlined.Dashboard)
    data object Study : Screen("study", R.string.nav_study, Icons.Filled.MenuBook, Icons.Outlined.MenuBook)
    data object Practice : Screen("practice", R.string.nav_practice, Icons.Filled.Quiz, Icons.Outlined.Quiz)
    data object Jobs : Screen("jobs", R.string.nav_jobs, Icons.Filled.Work, Icons.Outlined.WorkOutline)
    data object Focus : Screen("focus", R.string.nav_focus, Icons.Filled.Timer, Icons.Outlined.Timer)
    data object Forest : Screen("forest", R.string.nav_forest, Icons.Filled.Park, Icons.Outlined.Park)
    data object Settings : Screen("settings", R.string.nav_settings, Icons.Filled.Settings, Icons.Outlined.Settings)
}

val bottomNavItems = listOf(
    Screen.Dashboard,
    Screen.Study,
    Screen.Practice,
    Screen.Jobs,
    Screen.Focus
)

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun StudentStationNavHost(showOnboarding: Boolean, onOnboardingComplete: () -> Unit) {
    val navController = rememberNavController()
    val navBackStackEntry by navController.currentBackStackEntryAsState()
    val currentDestination = navBackStackEntry?.destination

    // Hide bottom bar during onboarding
    val showBottomBar = currentDestination?.route != "onboarding"

    Scaffold(
        bottomBar = {
            if (showBottomBar) {
                NavigationBar(
                    containerColor = MaterialTheme.colorScheme.surface,
                    tonalElevation = 0.dp
                ) {
                    bottomNavItems.forEach { screen ->
                        val selected = currentDestination?.hierarchy?.any { it.route == screen.route } == true

                        NavigationBarItem(
                            icon = {
                                Icon(
                                    imageVector = if (selected) screen.selectedIcon else screen.unselectedIcon,
                                    contentDescription = stringResource(screen.titleRes)
                                )
                            },
                            label = {
                                Text(
                                    text = stringResource(screen.titleRes),
                                    style = MaterialTheme.typography.labelSmall
                                )
                            },
                            selected = selected,
                            onClick = {
                                navController.navigate(screen.route) {
                                    popUpTo(navController.graph.findStartDestination().id) {
                                        saveState = true
                                    }
                                    launchSingleTop = true
                                    restoreState = true
                                }
                            },
                            colors = NavigationBarItemDefaults.colors(
                                selectedIconColor = MaterialTheme.colorScheme.primary,
                                selectedTextColor = MaterialTheme.colorScheme.primary,
                                indicatorColor = MaterialTheme.colorScheme.primaryContainer.copy(alpha = 0.3f)
                            )
                        )
                    }
                }
            }
        }
    ) { innerPadding ->
        NavHost(
            navController = navController,
            startDestination = if (showOnboarding) "onboarding" else Screen.Dashboard.route,
            modifier = Modifier.padding(innerPadding),
            enterTransition = { fadeIn() + slideInHorizontally { it / 4 } },
            exitTransition = { fadeOut() + slideOutHorizontally { -it / 4 } },
            popEnterTransition = { fadeIn() + slideInHorizontally { -it / 4 } },
            popExitTransition = { fadeOut() + slideOutHorizontally { it / 4 } }
        ) {
            composable("onboarding") {
                OnboardingScreen(
                    onComplete = {
                        onOnboardingComplete()
                        navController.navigate(Screen.Dashboard.route) {
                            popUpTo("onboarding") { inclusive = true }
                        }
                    }
                )
            }
            composable(Screen.Dashboard.route) { DashboardScreen() }
            composable(Screen.Study.route) { 
                StudyScreen(
                    onContentClick = { id ->
                        navController.navigate("content_viewer/$id")
                    },
                    onPlanClick = {
                        navController.navigate("study_plan")
                    }
                )
            }
            composable("study_plan") {
                StudyPlanScreen(
                    onNavigateBack = { navController.popBackStack() },
                    onTimetableClick = { navController.navigate("timetable") }
                )
            }
            composable("timetable") {
                TimetableScreen(
                    onNavigateBack = { navController.popBackStack() },
                    onStartFocusSession = { subjectId, subjectName ->
                        navController.navigate("focus_session/$subjectId/$subjectName")
                    }
                )
            }
            composable(
                route = "content_viewer/{contentId}",
                arguments = listOf(navArgument("contentId") { type = NavType.LongType })
            ) { backStackEntry ->
                val contentId = backStackEntry.arguments?.getLong("contentId") ?: return@composable
                ContentViewerScreen(
                    contentId = contentId,
                    onNavigateBack = { navController.popBackStack() }
                )
            }
            composable(Screen.Practice.route) { PracticeScreen() }
            composable(Screen.Jobs.route) { JobsScreen() }
            composable(Screen.Focus.route) { FocusScreen() }
            
            // Deep link from Timetable
            composable(
                route = "focus_session/{subjectId}/{subjectName}",
                arguments = listOf(
                    navArgument("subjectId") { type = NavType.LongType },
                    navArgument("subjectName") { type = NavType.StringType }
                )
            ) { backStackEntry ->
                val subjectId = backStackEntry.arguments?.getLong("subjectId")
                val subjectName = backStackEntry.arguments?.getString("subjectName")
                
                val viewModel: com.studentstation.app.presentation.features.focus.FocusViewModel = hiltViewModel()
                
                LaunchedEffect(subjectId, subjectName) {
                    if (subjectId != null && subjectName != null) {
                        viewModel.setSubject(subjectId, subjectName)
                        viewModel.startSession() // Auto-start the session!
                    }
                }
                FocusScreen(viewModel)
            }

            composable(Screen.Forest.route) { GamificationScreen() }
            composable(Screen.Settings.route) { SettingsScreen() }
        }
    }
}
