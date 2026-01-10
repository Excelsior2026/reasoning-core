import { useState, useEffect } from 'react'

const STORAGE_KEY = 'reasoning-core-settings'

const defaultSettings = {
  theme: 'light',
  autoSave: true,
  graphHeight: 600,
  defaultDomain: 'generic',
  showAdvanced: false,
}

export function SettingsPanel({ onSettingsChange }) {
  const [settings, setSettings] = useState(defaultSettings)
  const [isOpen, setIsOpen] = useState(false)

  useEffect(() => {
    loadSettings()
  }, [])

  const loadSettings = () => {
    try {
      const stored = localStorage.getItem(STORAGE_KEY)
      if (stored) {
        const parsed = JSON.parse(stored)
        setSettings({ ...defaultSettings, ...parsed })
      }
    } catch (err) {
      console.error('Failed to load settings:', err)
    }
  }

  const saveSettings = (newSettings) => {
    try {
      const updated = { ...settings, ...newSettings }
      localStorage.setItem(STORAGE_KEY, JSON.stringify(updated))
      setSettings(updated)
      if (onSettingsChange) {
        onSettingsChange(updated)
      }
    } catch (err) {
      console.error('Failed to save settings:', err)
    }
  }

  const updateSetting = (key, value) => {
    const newSettings = { ...settings, [key]: value }
    saveSettings(newSettings)
  }

  const resetSettings = () => {
    if (window.confirm('Reset all settings to default?')) {
      localStorage.removeItem(STORAGE_KEY)
      setSettings(defaultSettings)
      if (onSettingsChange) {
        onSettingsChange(defaultSettings)
      }
    }
  }

  if (!isOpen) {
    return (
      <button
        onClick={() => setIsOpen(true)}
        className="fixed bottom-4 right-4 p-3 bg-indigo-600 text-white rounded-full shadow-lg hover:bg-indigo-700 transition-colors"
        title="Settings"
      >
        ⚙️
      </button>
    )
  }

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full m-4 max-h-[90vh] overflow-y-auto">
        <div className="sticky top-0 bg-white border-b border-gray-200 p-4 flex justify-between items-center">
          <h2 className="text-xl font-semibold text-gray-900">Settings</h2>
          <button
            onClick={() => setIsOpen(false)}
            className="text-gray-400 hover:text-gray-600 text-2xl"
          >
            ×
          </button>
        </div>

        <div className="p-6 space-y-6">
          {/* Theme */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Theme
            </label>
            <select
              value={settings.theme}
              onChange={(e) => updateSetting('theme', e.target.value)}
              className="w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
            >
              <option value="light">Light</option>
              <option value="dark">Dark</option>
              <option value="auto">Auto (System)</option>
            </select>
          </div>

          {/* Default Domain */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Default Domain
            </label>
            <select
              value={settings.defaultDomain}
              onChange={(e) => updateSetting('defaultDomain', e.target.value)}
              className="w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
            >
              <option value="generic">Generic</option>
              <option value="medical">Medical</option>
              <option value="business">Business</option>
              <option value="meeting">Meeting/Agenda</option>
            </select>
          </div>

          {/* Graph Height */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Graph Height: {settings.graphHeight}px
            </label>
            <input
              type="range"
              min="400"
              max="1000"
              step="50"
              value={settings.graphHeight}
              onChange={(e) => updateSetting('graphHeight', parseInt(e.target.value))}
              className="w-full"
            />
          </div>

          {/* Auto Save */}
          <div className="flex items-center justify-between">
            <div>
              <label className="block text-sm font-medium text-gray-700">
                Auto-save History
              </label>
              <p className="text-xs text-gray-500 mt-1">
                Automatically save analysis results to history
              </p>
            </div>
            <label className="relative inline-flex items-center cursor-pointer">
              <input
                type="checkbox"
                checked={settings.autoSave}
                onChange={(e) => updateSetting('autoSave', e.target.checked)}
                className="sr-only peer"
              />
              <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-indigo-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-indigo-600"></div>
            </label>
          </div>

          {/* Show Advanced */}
          <div className="flex items-center justify-between">
            <div>
              <label className="block text-sm font-medium text-gray-700">
                Show Advanced Options
              </label>
              <p className="text-xs text-gray-500 mt-1">
                Display additional configuration options
              </p>
            </div>
            <label className="relative inline-flex items-center cursor-pointer">
              <input
                type="checkbox"
                checked={settings.showAdvanced}
                onChange={(e) => updateSetting('showAdvanced', e.target.checked)}
                className="sr-only peer"
              />
              <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-indigo-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-indigo-600"></div>
            </label>
          </div>

          {/* Reset */}
          <div className="pt-4 border-t border-gray-200">
            <button
              onClick={resetSettings}
              className="px-4 py-2 bg-red-600 text-white rounded-md hover:bg-red-700 transition-colors"
            >
              Reset to Defaults
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}
