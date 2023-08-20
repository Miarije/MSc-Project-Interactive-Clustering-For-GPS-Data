from code.main_menu import add_individual, initialize_interactive_clustering, run_analysis, revisit_clustering
import os


# welcome screen and options of main menu
def main():
  while True:
    os.system('cls')
    print("Welcome to the main menu of Interactive Clustering.\nPlease select an option.")
    print("[1] Add a new individual\n[2] Run clustering\n[3] Run cluster analysis\n[4] View or edit existing clustering\n[5] Exit program")

    user_input = input("Select the number: ")
    os.system('cls')
    if user_input.isdigit():
      choice = int(user_input)
      if choice == 1:
        add_individual()
      elif choice == 2:
        initialize_interactive_clustering()
      elif choice == 3:
        run_analysis()
      elif choice == 4:
        revisit_clustering()
      elif choice == 5:
        exit()
      else:
        print("Please enter a number between 1 and 4 to make your choice.")
    else:
      print("Please enter a number between 1 and 4 to make your choice.")


if __name__ == "__main__":
  main()
