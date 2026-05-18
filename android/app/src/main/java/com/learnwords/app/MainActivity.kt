package com.learnwords.app

import android.content.Intent
import android.os.Bundle
import android.widget.Toast
import androidx.appcompat.app.AppCompatActivity
import androidx.lifecycle.lifecycleScope
import androidx.navigation.NavController
import androidx.navigation.fragment.NavHostFragment
import androidx.navigation.ui.setupWithNavController
import com.google.android.material.bottomnavigation.BottomNavigationView
import com.learnwords.app.utils.NetworkResult
import com.learnwords.app.databinding.ActivityMainBinding
import kotlinx.coroutines.flow.first
import kotlinx.coroutines.launch

class MainActivity : AppCompatActivity() {

    private lateinit var binding: ActivityMainBinding
    private lateinit var navController: NavController

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        binding = ActivityMainBinding.inflate(layoutInflater)
        setContentView(binding.root)

        val navHostFragment = supportFragmentManager
            .findFragmentById(R.id.nav_host_fragment) as NavHostFragment
        navController = navHostFragment.navController

        val bottomNav: BottomNavigationView = binding.bottomNavigation
        bottomNav.setupWithNavController(navController)

        // Hide bottom nav on learn/auth screens
        navController.addOnDestinationChangedListener { _, destination, _ ->
            when (destination.id) {
                R.id.learnFragment, R.id.authFragment ->
                    bottomNav.visibility = android.view.View.GONE
                else ->
                    bottomNav.visibility = android.view.View.VISIBLE
            }
        }

        val handledDeepLink = handleTelegramAuthIntent(intent)

        // Check if user is logged in, redirect to auth if not
        lifecycleScope.launch {
            val prefs = (application as LearnWordsApp).preferencesManager
            val userId = prefs.userId.first()
            if (!handledDeepLink && userId.isBlank() && navController.currentDestination?.id != R.id.authFragment) {
                navController.navigate(R.id.authFragment)
            }
        }
    }

    override fun onNewIntent(intent: Intent) {
        super.onNewIntent(intent)
        setIntent(intent)
        handleTelegramAuthIntent(intent)
    }

    private fun handleTelegramAuthIntent(intent: Intent?): Boolean {
        val data = intent?.data ?: return false
        if (data.scheme != "learnwords" || data.host != "auth") return false

        val token = data.getQueryParameter("auth").orEmpty()
        val serverUrl = data.getQueryParameter("server").orEmpty()
        if (token.isBlank() || serverUrl.isBlank()) {
            Toast.makeText(this, "Некорректная ссылка входа", Toast.LENGTH_SHORT).show()
            return true
        }

        lifecycleScope.launch {
            val app = application as LearnWordsApp
            when (val result = app.repository.loginWithTelegramToken(serverUrl, token)) {
                is NetworkResult.Success -> {
                    val userId = result.data.userId.orEmpty()
                    if (userId.isNotBlank()) {
                        app.preferencesManager.saveUserId(userId)
                        app.preferencesManager.saveAuthMethod("Telegram")
                        Toast.makeText(this@MainActivity, "Вход выполнен", Toast.LENGTH_SHORT).show()
                        if (navController.currentDestination?.id != R.id.lessonsFragment) {
                            navController.navigate(R.id.lessonsFragment)
                        }
                    } else {
                        Toast.makeText(this@MainActivity, "Сервер не вернул User ID", Toast.LENGTH_SHORT).show()
                    }
                }
                is NetworkResult.Error -> {
                    Toast.makeText(this@MainActivity, result.message, Toast.LENGTH_LONG).show()
                    if (navController.currentDestination?.id != R.id.authFragment) {
                        navController.navigate(R.id.authFragment)
                    }
                }
                else -> Unit
            }
        }
        return true
    }

    override fun onSupportNavigateUp(): Boolean {
        return navController.navigateUp() || super.onSupportNavigateUp()
    }
}
