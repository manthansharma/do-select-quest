# DoSelect Quest
Repo for Do Select Quest (Backend Developer)

## Rest API Documentation
https://documenter.getpostman.com/view/2657815/doselect/6nBvVXt

## Changes from provided task
1. Instead of PATCH method to update image, POST request is used as it is stated in Django Documentation.
> Note that request.FILES will only contain data if the request method was POST and the `<form>` that posted the request has the attribute enctype="multipart/form-data". Otherwise, request.FILES will be empty.
> https://docs.djangoproject.com/en/1.11/topics/http/file-uploads/#basic-file-uploads
2. No database is used to store any information. File System functionality are used to simulate the whole design.
