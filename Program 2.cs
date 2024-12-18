using Newtonsoft.Json.Linq;
using Serilog;
using Serilog.Events;
using System;
using System.Collections.Generic;
using System.Data.SqlClient;
using System.Diagnostics;
using System.IO;
using System.Linq;
using System.Runtime.InteropServices;
using System.Threading;
using System.Threading.Tasks;
using System.Windows.Forms;
using System.Net.Http;
using System.DirectoryServices;
using System.DirectoryServices.AccountManagement;
using System.Configuration;
using System.Xml.Linq;
using System.Globalization;
using System.Security.Principal;
using Azure.Identity;
using Azure.Security.KeyVault.Secrets;
using System.Net.Sockets;
using Azure.Storage.Blobs;
using ConsoleApp2;
using Microsoft.Extensions.Azure;

namespace Autodesk_Tool2
{
    public class Program
    {
        // Global variables for configurations
        private static string logFilePath;
        //  private static string connectionString;
        private static string[] processNames;
        //private static string databaseFilePath;

        // Variables for tracking processes
        private static Dictionary<int, ProcessInfo> _currentProcesses = new Dictionary<int, ProcessInfo>();
        private static string configMessage;
        private static string title;
        private static int CheckIntervalInSeconds;
        private static bool _dialogActive;
        private static IntPtr _foregroundWindowHandle;
        private IntPtr _messageBoxWindowHandle;
        private static Program _instance;

        private static string userEmail;
        private static string countryCode;
        private static string userName;

        private static string keyVaultUrl;
        private static string tenantId;
        private static string clientId;
        private static string clientSecret;

        private static Dictionary<int, CustomMessageBox> customMessageBoxDict = new Dictionary<int, CustomMessageBox>();

        public static Program Instance => _instance ?? (_instance = new Program());

        [STAThread]
        static void Main()
        {
            bool createdNew = false;
            Mutex mutex = null;
            string mutexName = "WSP_Mutex_Autodesk_Accidental";

            // Validate user email
            if (!IsWspEmail())
            {
                Console.WriteLine("User does not have a wsp.com email address. Exiting.");
                return;
            }

            try
            {
                mutex = new Mutex(true, mutexName, out createdNew);

                if (!createdNew)
                {
                    Console.WriteLine("Another instance is already running. Exiting.");
                    return;
                }

                Console.WriteLine("Application is running.");

                // Start process monitoring
                Thread monitoringThread = new Thread(Instance.MonitorProcesses);
                monitoringThread.Start();

                // Hook Revit application activation event
                HookRevitAppActivationEvent();

                monitoringThread.Join();

                UnhookRevitAppActivationEvent();
            }
            finally
            {
                if (createdNew && mutex != null)
                {
                    mutex.ReleaseMutex();
                    mutex.Dispose();
                }
            }
        }

        // Method to load the JSON configuration
        private static void LoadConfiguration(string toolName)
        {
            try
            {
                // Read the blob content
                string blobContent = GetConfigFromBlob() ?? throw new ArgumentException("Blob content cannot be empty");

                // Parse the JSON string into a JObject
                JObject jsonContent = JObject.Parse(blobContent);

                // Get two letter country code
                countryCode = GetCountryCode();

                // Get config of user's country
                JObject config = (JObject)jsonContent[countryCode];

                // Load General Settings
                CheckIntervalInSeconds = (int)config["GeneralSettings"]["CheckIntervalInSeconds"];

                // Get the Windows directory path dynamically
                string windowsPath = Environment.GetFolderPath(Environment.SpecialFolder.Windows);

                // Construct the base folder path dynamically
                string baseFolderPath = Path.Combine(windowsPath, "WSP", "WSP_Software_Optimization_Tool");

                // Load tool-specific settings dynamically
                logFilePath = Path.Combine(baseFolderPath, (string)config.SelectToken($"AutodeskSettings.ToolsConfig.{toolName}.LogFilePath"));

                // Load process names and connection string
                processNames = config["AutodeskSettings"]["ProcessNames"].ToObject<string[]>();

                // Get Message and title from config
                configMessage = (string)config["AutodeskSettings"]["Accidental"]["Message"];
                title = (string)config["AutodeskSettings"]["Accidental"]["Title"];

                // Get KeyVault settings
                keyVaultUrl = config["KeyVaultSettings"]["KeyVaultUrl"].ToString();
                tenantId = config["KeyVaultSettings"]["TenantId"].ToString();
                clientId = config["KeyVaultSettings"]["ClientId"].ToString();
                clientSecret = config["KeyVaultSettings"]["ClientSecret"].ToString();

                // Load database file path
                //databaseFilePath = Path.Combine(exeDirectory, (string)config["GeneralSettings"]["DatabaseFilePath"]);

                // Ensure directories for log file and database file exist
                EnsureDirectoryExists(Path.GetDirectoryName(logFilePath));
                //EnsureDirectoryExists(Path.GetDirectoryName(databaseFilePath));

                Console.WriteLine("Configuration loaded successfully.");
            }
            catch (Exception ex)
            {
                Console.WriteLine($"Error loading configuration: {ex.Message}");
                throw;
            }
        }

        private static string GetCountryCode()
        {
            // Default country code and region
            string countryCode = "Unknown";

            // Get the country code from Active Directory
            using (PrincipalContext context = new PrincipalContext(ContextType.Domain))
            {
                UserPrincipal user = UserPrincipal.FindByIdentity(context, Environment.UserName);
                if (user != null && user.EmailAddress != null && user.EmailAddress.EndsWith("@wsp.com", StringComparison.OrdinalIgnoreCase))
                {
                    // Retrieve country code from Active Directory
                    countryCode = user.GetUnderlyingObject() is DirectoryEntry directoryEntry && directoryEntry.Properties.Contains("c")
                        ? directoryEntry.Properties["c"][0].ToString()
                        : "Unknown";

                    // Log the retrieved country code for debugging
                    Console.WriteLine($"Country Code retrieved: {countryCode}");
                }
            }
            return countryCode;
        }

        private static string GetConfigFromBlob()
        {
            try
            {
                // LAC Azure Blob Storage
                string blobName = "appsettings.json";
                string storageAccountName = "sasoftwaretoken";
                string storageAccountKey = "KDJFLKFJSDKLFJ C,XVMRGJEGE==&ERJTEKG*==KGG3=";
                string containerName = "jsoncontainer";

                string connectionString = $"DefaultEndpointsProtocol=https;AccountName={storageAccountName};AccountKey={storageAccountKey};EndpointSuffix=core.windows.net";
                var blobClient = new BlobClient(connectionString, containerName, blobName);

                var response = blobClient.Download();

                string content = null;
                // Read the blob content
                using (var reader = new StreamReader(response.Value.Content))
                {
                    content = reader.ReadToEnd();
                }
                return content;
            }
            catch (Exception ex)
            {
                Console.WriteLine($"Error while connecting to Azure Blob Storage: {ex}");
                throw;
            }
        }

        // Helper method to ensure a directory exists
        private static void EnsureDirectoryExists(string directoryPath)
        {
            if (!string.IsNullOrEmpty(directoryPath) && !Directory.Exists(directoryPath))
            {
                Directory.CreateDirectory(directoryPath);
            }
        }

        // Helper method to initialize the log file if it doesn't exist
        private static void InitializeLogFile(string logFilePath)
        {
            if (!File.Exists(logFilePath))
            {
                using (FileStream fs = File.Create(logFilePath)) { }
                Console.WriteLine($"Log file created at {logFilePath}");
            }
        }

        // Method to check if the user's email is in the WSP domain
        public static bool IsWspEmail()
        {
            using (PrincipalContext context = new PrincipalContext(ContextType.Domain))
            {
                UserPrincipal user = UserPrincipal.FindByIdentity(context, Environment.UserName);
                if (user != null && user.EmailAddress != null && user.EmailAddress.EndsWith("@wsp.com", StringComparison.OrdinalIgnoreCase))
                {
                    userName = user.DisplayName ?? user.Name;
                    userEmail = user.EmailAddress;

                    countryCode = user.GetUnderlyingObject() is DirectoryEntry directoryEntry && directoryEntry.Properties.Contains("c")
                        ? directoryEntry.Properties["c"][0].ToString()
                        : "Unknown";

                    return true;
                }
            }

            userName = string.Empty;
            userEmail = string.Empty;
            countryCode = string.Empty;
            return false;
        }

        private Program()
        {
            _dialogActive = false;
            _foregroundWindowHandle = GetForegroundWindow();
            _messageBoxWindowHandle = IntPtr.Zero;
        }


        // Monitor processes and handle activity
        private void MonitorProcesses()
        {
            LoadConfiguration("Autodesk_Tool2");

            // Close opened log files
            Log.CloseAndFlush();

            // Initialize log files
            Log.Logger = new LoggerConfiguration()
                .MinimumLevel.Debug()
                .WriteTo.Console(restrictedToMinimumLevel: LogEventLevel.Information)
                .WriteTo.File(logFilePath, rollingInterval: RollingInterval.Day, restrictedToMinimumLevel: LogEventLevel.Information)
                .CreateLogger();

            while (true)
            {
                // Close unhandled message boxes
                CloseUnhandledMessageBox();

                foreach (var processName in processNames)
                {
                    if (IsProcessRunning(processName))
                    {
                        Process[] processes = Process.GetProcessesByName(processName);

                        foreach (var process in processes)
                        {
                            if (!_currentProcesses.ContainsKey(process.Id))
                            {
                                _currentProcesses[process.Id] = new ProcessInfo
                                {
                                    ProcessName = processName,
                                    LaunchTime = DateTime.Now
                                };

                                BringProcessApplicationDialogToFront(processName, process);
                            }
                        }
                    }
                    else
                    {
                        _currentProcesses = _currentProcesses
                            .Where(p => p.Value.ProcessName != processName)
                            .ToDictionary(p => p.Key, p => p.Value);
                    }
                }
                Thread.Sleep(CheckIntervalInSeconds * 1000);
            }
        }

        private static void CloseUnhandledMessageBox()
        {
            // Close messageboxes of already terminated applications
            var messageBoxListCopy = new Dictionary<int, CustomMessageBox>(customMessageBoxDict);
            List<int> removeKey = new List<int>();

            foreach (var customMessageBox in messageBoxListCopy)
            {
                if (!ProcessIdExists(customMessageBox.Key))
                {
                    if (customMessageBox.Value.InvokeRequired)
                    {
                        customMessageBox.Value.Invoke(new Action(() => customMessageBox.Value.Close()));
                    }
                    else
                    {
                        customMessageBox.Value.Close();
                    }
                    removeKey.Add(customMessageBox.Key);
                }
            }

            foreach (var key in removeKey)
            {
                customMessageBoxDict.Remove(key);
            }
        }
        static bool ProcessIdExists(int processId)
        {
            try
            {
                // Attempt to get the process by ID
                Process process = Process.GetProcessById(processId);
                return process != null;
            }
            catch (ArgumentException)
            {
                // If an ArgumentException is thrown, the process does not exist
                return false;
            }
        }

        // Check if a process is running
        private static bool IsProcessRunning(string processName)
        {
            return Process.GetProcessesByName(processName).Length > 0;
        }

        // Method to display the application dialog
        private static async Task BringProcessApplicationDialogToFront(string processName, Process process)
        {
            string processTitle = await ProcessTitleFetcher.GetProcessTitleAsync(process.Id.ToString());

            string modifiedProcessName = processName switch
            {
                "Roamer" => "Navisworks",
                "revit" => "Revit",
                "acad" => "AutoCAD",
                _ => processName
            };

            string modifiedProcessNameTitle = processTitle != "" ? modifiedProcessName + " - " + processTitle : modifiedProcessName;

            Thread messageBoxThread = new Thread(() =>
            {
                string[] configMessageSplit = configMessage.Split(new string[] { "{processname}" }, StringSplitOptions.None);
                string message = $"{configMessageSplit[0]}{modifiedProcessNameTitle}{configMessageSplit[1]}";

                DialogResult result = DialogResult.No;
                try
                {
                    CustomMessageBox customMessageBox = new CustomMessageBox(message, title, MessageBoxButtons.YesNo, MessageBoxIcon.Warning);
                    customMessageBoxDict.Add(process.Id, customMessageBox);
                    SetForegroundWindow(customMessageBox.Handle);
                    FlashWindow(customMessageBox.Handle, true);

                    result = customMessageBox.ShowDialog();
                }
                catch (Exception ex)
                {
                    Log.Error(ex, "Error occurred while displaying message box.");
                }

                DateTime launchTime = _currentProcesses.ContainsKey(process.Id) ? _currentProcesses[process.Id].LaunchTime : DateTime.Now;
                DateTime closeTime = DateTime.Now;
                double maxIdleTime = (closeTime - launchTime).TotalMinutes;

                if (result == DialogResult.No && !process.HasExited)
                {
                    Log.Information($"User clicked No. Killing process... {processName}");
                    process.Kill();
                    Log.Information($"Application {processName} will be closed.");
                }
                else if (result == DialogResult.Yes)
                {
                    Log.Information($"User clicked Yes. Continuing process... {processName}");
                }

                Task.Run(() => InsertDataIntoDatabase(modifiedProcessName, processTitle, process.Id, maxIdleTime, result == DialogResult.Yes ? "Yes" : "No", closeTime)).Wait();
            });

            messageBoxThread.SetApartmentState(ApartmentState.STA);
            messageBoxThread.Start();
        }

        // Get process title based on ID
        private static string GetProcessTitle(string processId)
        {
            if (int.TryParse(processId, out int id))
            {
                try
                {
                    Process process = Process.GetProcessById(id);
                    _foregroundWindowHandle = GetForegroundWindow();
                    return process.MainWindowTitle;
                }
                catch (Exception ex)
                {
                    Log.Error(ex, "Error fetching process title.");
                }
            }
            return string.Empty;
        }

        private static string GetUserRegion()
        {
            // Default country code and region
            string countryCode = "Unknown";
            string region = "EMEAI"; // Default to EMEAI if region is not determined

            // Get the country code from Active Directory
            using (PrincipalContext context = new PrincipalContext(ContextType.Domain))
            {
                UserPrincipal user = UserPrincipal.FindByIdentity(context, Environment.UserName);
                if (user != null && user.EmailAddress != null && user.EmailAddress.EndsWith("@wsp.com", StringComparison.OrdinalIgnoreCase))
                {
                    // Retrieve country code from Active Directory
                    countryCode = user.GetUnderlyingObject() is DirectoryEntry directoryEntry && directoryEntry.Properties.Contains("c")
                        ? directoryEntry.Properties["c"][0].ToString()
                        : "Unknown";

                    // Log the retrieved country code for debugging
                    Console.WriteLine($"Country Code retrieved: {countryCode}");

                    // Attempt to map the country code to a region
                    try
                    {
                        region = GetRegionByCountryCode(countryCode);
                        Console.WriteLine($"Mapped Region: {region}");
                    }
                    catch (Exception ex)
                    {
                        Console.WriteLine($"Error while mapping country code '{countryCode}' to region: {ex.Message}");
                    }
                }
            }
            return region;
        }

        // Insert data into database (SQL or SQLite)
        private static async Task InsertDataIntoDatabase(string modifiedProcessName, string processTitle, int processId, double maxIdleTime, string userAction, DateTime closeTime)
        {
            string tableName = "WSP_SOFTWARE_OPTIMIZATION";
            string connectionString;

            // Authenticate using Key Vault details
            var clientSecretCredential = new ClientSecretCredential(tenantId, clientId, clientSecret);

            // Create a SecretClient to access Key Vault
            var secretClient = new SecretClient(new Uri(keyVaultUrl), clientSecretCredential);

            // Retrieve a secret from Key Vault
            try
            {
                KeyVaultSecret secret = secretClient.GetSecret("cred");
                Console.WriteLine($"Secret Value: {secret.Value}");
                connectionString = secret.Value;
            }
            catch (Exception ex)
            {
                Console.WriteLine($"Error: {ex.Message}");
                connectionString = "";
            }

            if (await IsConnectedToInternet())
            {
                try
                {
                    using (var connection = new SqlConnection(connectionString))
                    {
                        await connection.OpenAsync();
                        string query = $@"INSERT INTO {tableName} (ProcessName, ProcessId, MaxIdleTime, MachineName, ProcessTitle, UserName, CreatedDate, StatusType, UserAction, Publisher, UserEmail, CountryCode, UserId)
                            VALUES (@ProcessName, @ProcessId, @MaxIdleTime, @MachineName, @ProcessTitle, @UserName, @CreatedDate, @StatusType, @UserAction, @Publisher, @UserEmail, @CountryCode, @UserId)";

                        using (var command = new SqlCommand(query, connection))
                        {
                            command.Parameters.AddWithValue("@ProcessName", modifiedProcessName);
                            command.Parameters.AddWithValue("@ProcessId", processId);
                            command.Parameters.AddWithValue("@MaxIdleTime", maxIdleTime);
                            command.Parameters.AddWithValue("@MachineName", Environment.MachineName);
                            command.Parameters.AddWithValue("@ProcessTitle", processTitle);
                            command.Parameters.AddWithValue("@UserName", userName);
                            command.Parameters.AddWithValue("@CreatedDate", closeTime.ToString("yyyy-MM-dd HH:mm:ss"));
                            command.Parameters.AddWithValue("@StatusType", "AccidentalMonitor");
                            command.Parameters.AddWithValue("@UserAction", userAction);
                            command.Parameters.AddWithValue("@Publisher", "Autodesk");
                            command.Parameters.AddWithValue("@UserEmail", userEmail);
                            command.Parameters.AddWithValue("@CountryCode", countryCode);
                            command.Parameters.AddWithValue("@UserId", Environment.UserName);

                            await command.ExecuteNonQueryAsync();
                        }
                    }
                }
                catch (Exception ex)
                {
                    Log.Error(ex, "SQL Server error occurred.");
                }
            }
            else
            {
                //try
                //{
                //    InitializeDatabase();

                //    using (var connection = new SQLiteConnection($"Data Source={databaseFilePath};Version=3;"))
                //    {
                //        await connection.OpenAsync();
                //        string query = $@"INSERT INTO {tableName} (ProcessName, ProcessId, MaxIdleTime, MachineName, ProcessTitle, UserName, CreatedDate, StatusType, UserAction, Publisher, UserEmail, CountryCode, UserId)
                //            VALUES (@ProcessName, @ProcessId, @MaxIdleTime, @MachineName, @ProcessTitle, @UserName, @CreatedDate, @StatusType, @UserAction, @Publisher, @UserEmail, @CountryCode, @UserId)";

                //        using (var command = new SQLiteCommand(query, connection))
                //        {
                //            command.Parameters.AddWithValue("@ProcessName", modifiedProcessName ?? string.Empty);
                //            command.Parameters.AddWithValue("@ProcessId", processId);
                //            command.Parameters.AddWithValue("@MaxIdleTime", maxIdleTime);
                //            command.Parameters.AddWithValue("@MachineName", Environment.MachineName);
                //            command.Parameters.AddWithValue("@ProcessTitle", processTitle ?? string.Empty);
                //            command.Parameters.AddWithValue("@UserName", userName ?? string.Empty);
                //            command.Parameters.AddWithValue("@CreatedDate", closeTime.ToString("yyyy-MM-dd HH:mm:ss"));
                //            command.Parameters.AddWithValue("@StatusType", "AccidentalMonitor");
                //            command.Parameters.AddWithValue("@UserAction", userAction ?? string.Empty);
                //            command.Parameters.AddWithValue("@Publisher", "Autodesk");
                //            command.Parameters.AddWithValue("@UserEmail", userEmail ?? string.Empty);
                //            command.Parameters.AddWithValue("@CountryCode", countryCode ?? string.Empty);
                //            command.Parameters.AddWithValue("@UserId", Environment.UserName ?? string.Empty);

                //            await command.ExecuteNonQueryAsync();
                //        }
                //    }
                //}
                //catch (Exception ex)
                //{
                //    Log.Error(ex, "SQLite error occurred.");
                //}
            }
        }

        // Check if the system is connected to the internet
        private static async Task<bool> IsConnectedToInternet()
        {
            return await IsInternetAvailable();
        }

        public static async Task<bool> IsInternetAvailable()
        {
            try
            {
                using (var httpClient = new HttpClient())
                {
                    httpClient.Timeout = TimeSpan.FromSeconds(5);
                    var response = await httpClient.GetAsync("http://www.msftncsi.com/ncsi.txt");
                    if (response.IsSuccessStatusCode)
                    {
                        string responseText = await response.Content.ReadAsStringAsync();
                        return responseText == "Microsoft NCSI";
                    }
                    return false;
                }
            }
            catch
            {
                return false;
            }
        }

        private static string GetTableNameByRegion()
        {
            string countryCode = "Unknown";

            // Default region if country code is not found
            string defaultRegion = "EMEAI";
            string region = defaultRegion;

            // Get the country code from Active Directory
            using (PrincipalContext context = new PrincipalContext(ContextType.Domain))
            {
                UserPrincipal user = UserPrincipal.FindByIdentity(context, Environment.UserName);
                if (user != null && user.EmailAddress != null && user.EmailAddress.EndsWith("@wsp.com", StringComparison.OrdinalIgnoreCase))
                {
                    countryCode = user.GetUnderlyingObject() is DirectoryEntry directoryEntry && directoryEntry.Properties.Contains("c")
                        ? directoryEntry.Properties["c"][0].ToString()
                        : "Unknown";

                    // Log the retrieved country code for debugging
                    Console.WriteLine($"Country Code retrieved: {countryCode}");

                    // Attempt to map the country code to a region
                    try
                    {
                        region = GetRegionByCountryCode(countryCode);
                        Console.WriteLine($"Mapped Region: {region}");
                    }
                    catch (Exception ex)
                    {
                        // Log the error for debugging
                        Console.WriteLine($"Error while mapping country code '{countryCode}' to region: {ex.Message}");
                    }
                }
            }

            // Return the table name based on the resolved region
            return region switch
            {
                "AMER" => "WSP_AMER", // CO, CL, BR 
                "APAC" => "WSP_APAC", // IN
                "EMEAI" => "WSP_EMEAI", // SA, AE
                _ => "WSP_APAC"
            };
        }

        // Helper method to map country codes to regions
        private static string GetRegionByCountryCode(string countryCode)
        {
            // Mapping of country codes to regions
            var countryToRegion = new Dictionary<string, string>(StringComparer.OrdinalIgnoreCase)
    {
        // AMER region countries
        { "US", "AMER" }, { "CA", "AMER" }, { "MX", "AMER" }, { "BR", "AMER" }, { "AR", "AMER" },
        { "CO", "AMER" }, { "CL", "AMER" }, { "PE", "AMER" }, { "VE", "AMER" },

        // APAC region countries
        { "AU", "APAC" }, { "JP", "APAC" }, { "CN", "APAC" }, { "IN", "APAC" }, { "SG", "APAC" },
        { "NZ", "APAC" }, { "KR", "APAC" }, { "MY", "APAC" }, { "ID", "APAC" }, { "TH", "APAC" },
        { "PH", "APAC" }, { "VN", "APAC" }, { "HK", "APAC" }, { "TW", "APAC" },

        // EMEAI region countries
        { "GB", "EMEAI" }, { "DE", "EMEAI" }, { "FR", "EMEAI" }, { "IT", "EMEAI" }, { "ES", "EMEAI" },
        { "NL", "EMEAI" }, { "BE", "EMEAI" }, { "SE", "EMEAI" }, { "NO", "EMEAI" }, { "FI", "EMEAI" },
        { "RU", "EMEAI" }, { "SA", "EMEAI" }, { "AE", "EMEAI" }, { "ZA", "EMEAI" }, { "EG", "EMEAI" },
        { "TR", "EMEAI" },

        // Other country codes...
    };

            // Check if the country code exists in the dictionary
            if (countryToRegion.TryGetValue(countryCode, out var region))
            {
                return region;
            }

            // Log if the country code wasn't found
            Console.WriteLine($"Country code '{countryCode}' not found in the mapping, defaulting to EMEAI.");

            // Default to EMEAI if no matching country code is found
            return "EMEAI";
        }

        //// Initialize the SQLite database if it doesn't exist
        //private static void InitializeDatabase()
        //{
        //    if (!File.Exists(databaseFilePath))
        //    {
        //        SQLiteConnection.CreateFile(databaseFilePath);

        //        using (SQLiteConnection connection = new SQLiteConnection($"Data Source={databaseFilePath};Version=3;"))
        //        {
        //            connection.Open();

        //            string tableName = GetTableNameByRegion();
        //            string sqlCreateTable = $@"
        //                CREATE TABLE IF NOT EXISTS {tableName} (
        //                    Id INTEGER PRIMARY KEY AUTOINCREMENT,
        //                    ProcessName TEXT,
        //                    ProcessId INTEGER,
        //                    MaxIdleTime REAL,
        //                    MachineName TEXT,
        //                    ProcessTitle TEXT,
        //                    UserName TEXT,
        //                    UserEmail TEXT,
        //                    CountryCode TEXT,
        //                    UserId TEXT,
        //                    CreatedDate TEXT,
        //                    StatusType TEXT,
        //                    UserAction TEXT,
        //                    Publisher TEXT
        //                );";

        //            using (SQLiteCommand command = new SQLiteCommand(sqlCreateTable, connection))
        //            {
        //                command.ExecuteNonQuery();
        //                Log.Information($"Table {tableName} created or ensured in the database.");
        //            }
        //        }
        //    }
        //}

        // P/Invoke methods for interacting with the Windows UI
        [DllImport("user32.dll")]
        private static extern bool EnableWindow(IntPtr hWnd, bool enable);

        [DllImport("user32.dll")]
        private static extern IntPtr GetForegroundWindow();

        [DllImport("user32.dll")]
        private static extern bool SetForegroundWindow(IntPtr hWnd);

        [DllImport("user32.dll")]
        static extern bool FlashWindow(IntPtr hwnd, bool bInvert);

        [DllImport("user32.dll")]
        private static extern IntPtr FindWindow(string lpClassName, string lpWindowName);

        private const int SW_RESTORE = 9;

        [DllImport("user32.dll", CharSet = CharSet.Auto, SetLastError = true)]
        private static extern IntPtr SetWinEventHook(uint eventMin, uint eventMax, IntPtr hmodWinEventProc,
            WinEventDelegate pfnWinEventProc, uint idProcess, uint idThread, uint dwFlags);

        [DllImport("user32.dll", CharSet = CharSet.Auto, SetLastError = true)]
        private static extern bool UnhookWinEvent(IntPtr hWinEventHook);

        private const uint EVENT_OBJECT_NAMECHANGE = 0x800C;

        private delegate void WinEventDelegate(IntPtr hWinEventHook, uint eventType, IntPtr hwnd, int idObject,
            int idChild, uint dwEventThread, uint dwmsEventTime);

        private static readonly WinEventDelegate RevitAppActivationDelegate = RevitAppActivationCallback;

        private static IntPtr _revitAppActivationEventHook;

        private static void HookRevitAppActivationEvent()
        {
            _revitAppActivationEventHook = SetWinEventHook(EVENT_OBJECT_NAMECHANGE, EVENT_OBJECT_NAMECHANGE, IntPtr.Zero,
                RevitAppActivationDelegate, 0, 0, 0);
        }

        private static void UnhookRevitAppActivationEvent()
        {
            UnhookWinEvent(_revitAppActivationEventHook);
        }

        private static void RevitAppActivationCallback(IntPtr hWinEventHook, uint eventType, IntPtr hwnd, int idObject, int idChild, uint dwEventThread, uint dwmsEventTime)
        {
            if (eventType == EVENT_OBJECT_NAMECHANGE)
            {
                IntPtr messageBoxWindowHandle = Instance._messageBoxWindowHandle;
                if (messageBoxWindowHandle != IntPtr.Zero && GetForegroundWindow() == hwnd)
                {
                    Instance._messageBoxWindowHandle = hwnd;
                    SetForegroundWindow(messageBoxWindowHandle);
                }
            }
        }

        private void CreateLogFile(string logMessage)
        {
            if (!string.IsNullOrEmpty(logMessage))
            {
                Log.Information(logMessage);
            }
        }
    }

    public class ProcessTitleFetcher
    {
        public static async Task<string> GetProcessTitleAsync(string processId, int timeoutInSeconds = 1)
        {
            if (!int.TryParse(processId, out int id))
            {
                Console.WriteLine("Error: Invalid process ID.");
                return string.Empty;
            }

            try
            {
                using (Process process = Process.GetProcessById(id))
                {
                    if (!string.IsNullOrEmpty(process.MainWindowTitle))
                    {
                        return process.MainWindowTitle;
                    }

                    int elapsedTime = 0;
                    const int delayInterval = 1000; // 1 second
                    while (elapsedTime < timeoutInSeconds * 1000)
                    {
                        await Task.Delay(delayInterval);
                        elapsedTime += delayInterval;
                        process.Refresh();

                        if (!string.IsNullOrEmpty(process.MainWindowTitle))
                        {
                            return process.MainWindowTitle;
                        }
                    }

                    Console.WriteLine($"Timeout: Process window title for ID {id} not available after {timeoutInSeconds} seconds.");
                }
            }
            catch (ArgumentException)
            {
                Console.WriteLine($"Error: Process with ID {id} does not exist.");
            }
            catch (InvalidOperationException)
            {
                Console.WriteLine($"Error: Process with ID {id} has exited.");
            }
            catch (Exception ex)
            {
                Console.WriteLine($"Unexpected error: {ex.Message}");
            }

            return string.Empty;
        }
    }

    public class ProcessInfo
    {
        public string ProcessName { get; set; }
        public DateTime LaunchTime { get; set; }
    }
}
