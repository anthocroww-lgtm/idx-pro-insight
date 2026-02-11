package com.example.myapplication

import android.annotation.SuppressLint
import android.os.Bundle
import android.view.View
import android.webkit.CookieManager
import android.webkit.WebChromeClient
import android.webkit.WebSettings
import android.webkit.WebView
import android.webkit.WebViewClient
import android.widget.ProgressBar
import androidx.activity.ComponentActivity
import androidx.activity.OnBackPressedCallback
import androidx.activity.OnBackPressedDispatcher

/**
 * WebView wrapper untuk aplikasi Streamlit (IDX-Pro Insight).
 * Versi web direferensi: 1.3.0 (sinkron dengan deploy terbaru).
 * - Back: OnBackPressedDispatcher (tanpa deprecation).
 * - Progress bar saat loading.
 * - Cookie & WebViewClient diperbaiki untuk redirect/HTTPS.
 */
class MainActivity : ComponentActivity() {

    private lateinit var webView: WebView
    private lateinit var progressBar: ProgressBar

    @SuppressLint("SetJavaScriptEnabled")
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_main)

        webView = findViewById(R.id.webView)
        progressBar = findViewById(R.id.progressBar)

        // Cookie agar login/session Streamlit jalan
        CookieManager.getInstance().apply {
            setAcceptCookie(true)
            setAcceptThirdPartyCookies(webView, true)
        }

        val settings: WebSettings = webView.settings
        settings.javaScriptEnabled = true
        settings.domStorageEnabled = true
        settings.databaseEnabled = true
        settings.useWideViewPort = true
        settings.loadWithOverviewMode = true
        settings.cacheMode = WebSettings.LOAD_DEFAULT

        // Tetap di dalam app, tangani redirect dengan benar
        webView.webViewClient = object : WebViewClient() {
            override fun shouldOverrideUrlLoading(view: WebView?, url: String?): Boolean {
                if (!url.isNullOrBlank()) view?.loadUrl(url)
                return true
            }
        }

        // Progress bar: tampil saat loading, hilang saat selesai
        webView.webChromeClient = object : WebChromeClient() {
            override fun onProgressChanged(view: WebView?, newProgress: Int) {
                if (newProgress < 100) {
                    progressBar.visibility = View.VISIBLE
                    progressBar.progress = newProgress
                } else {
                    progressBar.visibility = View.GONE
                }
            }
        }

        // Back handling (cara modern, tanpa deprecation)
        onBackPressedDispatcher.addCallback(this, object : OnBackPressedCallback(true) {
            override fun handleOnBackPressed() {
                if (this@MainActivity::webView.isInitialized && webView.canGoBack()) {
                    webView.goBack()
                } else {
                    isEnabled = false
                    onBackPressedDispatcher.onBackPressed()
                }
            }
        })

        // GANTI dengan URL Streamlit Anda (setelah deploy web terbaru, Android tampil sama)
        val appUrl = "https://idx-pro-insight-22.streamlit.app"

        // Restore state agar setelah refresh/rotate app tetap login (cookie & halaman tidak hilang)
        if (savedInstanceState != null) {
            webView.restoreState(savedInstanceState)
        } else {
            webView.loadUrl(appUrl)
        }
    }

    override fun onSaveInstanceState(outState: Bundle) {
        super.onSaveInstanceState(outState)
        if (this::webView.isInitialized) {
            webView.saveState(outState)
        }
    }
}
