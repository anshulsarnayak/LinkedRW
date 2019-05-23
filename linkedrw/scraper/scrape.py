import argparse
import json

from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.support.ui import WebDriverWait

from linkedrw.exceptions import LoginError
from linkedrw.globals import *
from accomplishment import get_accomplishment_details
from background import get_background_details
from personal import get_personal_details


def scrape(email, password, **kwargs):
    driver = webdriver.Chrome()
    driver.get('https://www.linkedin.com/login/')

    # Login to LinkedIn
    driver.find_element_by_id('username').send_keys(email)
    driver.find_element_by_id('password').send_keys(password)
    driver.find_element_by_class_name('login__form_action_container').submit()

    html = driver.page_source.lower()
    if any(x in html for x in ['we don\'t recognize that email', 'that\'s not the right password']):
        driver.quit()

        raise LoginError('Invalid login credentials')

    # Skip adding a phone number
    try:
        driver.find_element_by_css_selector('.ember-view.cp-add-phone')
        driver.find_element_by_class_name('secondary-action').click()
    except NoSuchElementException:
        pass

    # Navigate to profile page
    driver.find_element_by_xpath("//a[@data-control-name='identity_welcome_message']").click()
    WebDriverWait(driver, TIMEOUT).until(ec.presence_of_element_located((By.ID, 'oc-background-section')))

    profile = {
        NAME: get_personal_details(driver, NAME),
        POSITION: get_personal_details(driver, POSITION),
        CONTACT: get_personal_details(driver, CONTACT),
        SUMMARY: get_personal_details(driver, SUMMARY),
        EXPERIENCE: get_background_details(driver, By.ID, 'experience-section', EXPERIENCE),
        EDUCATION: get_background_details(driver, By.ID, 'education-section', EDUCATION),
        VOLUNTEERING: get_background_details(
            driver, By.CSS_SELECTOR, '.pv-profile-section.volunteering-section.ember-view', VOLUNTEERING),
        SKILLS: get_background_details(
            driver, By.CSS_SELECTOR,
            '.pv-profile-section.pv-skill-categories-section.artdeco-container-card.ember-view', SKILLS),
        PROJECTS: get_accomplishment_details(driver, PROJECTS),
        PUBLICATIONS: get_accomplishment_details(driver, PUBLICATIONS),
        HONORS: get_accomplishment_details(driver, HONORS),
        LANGUAGES: get_accomplishment_details(driver, LANGUAGES)
    }

    driver.quit()
    with open('profile.json', 'w') as f:
        json.dump(profile, f, indent=4)

    return profile


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Scrape your LinkedIn profile')
    parser.set_defaults(method=scrape)

    parser.add_argument('email', help='Your LinkedIn login email')
    parser.add_argument('password', help='Your LinkedIn login password')

    args = parser.parse_args()
    args.method(**vars(args))
